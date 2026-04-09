"""Resume generation and management API routes."""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from backend.database import get_db
from backend.models.user import User
from backend.schemas.resume import ResumeGenerateRequest, ResumeGenerateResponse, ResumeListItem
from backend.utils.auth import get_current_user
from backend.services.resume_service import resume_service
from backend.services.file_service import file_service
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resume", tags=["Resume"])

# Rate limiting - store request counts per user per action
_rate_limit_cache = {}

_PLACEHOLDER_NAMES = {"your name", "first last", "full name", "name"}


def _parsed_resume_input(req: "ValidatedResumeGenerateRequest") -> dict:
    """Best-effort extraction of structured resume input from the request."""
    if req.resume_data:
        if isinstance(req.resume_data, BaseModel):
            if hasattr(req.resume_data, "model_dump"):
                return req.resume_data.model_dump()
            return req.resume_data.dict()
        return dict(req.resume_data)

    if req.existing_resume:
        try:
            parsed = json.loads(req.existing_resume)
            if isinstance(parsed, dict):
                return parsed
        except (TypeError, ValueError):
            pass

    return {}


def _is_placeholder_name(value: str) -> bool:
    """Detect generic placeholder names that should be replaced by real user data."""
    if not value:
        return True
    normalized = value.strip().lower()
    return normalized in _PLACEHOLDER_NAMES


def _merge_resume_content(content: dict, fallback_data: dict, current_user: User) -> dict:
    """Merge AI output with submitted form data so previews/downloads always stay populated."""
    merged = dict(content) if isinstance(content, dict) else {}
    fallback_data = fallback_data or {}

    if _is_placeholder_name(merged.get("full_name")):
        merged["full_name"] = (
            fallback_data.get("full_name")
            or current_user.full_name
            or merged.get("full_name")
            or "Your Name"
        )

    fallback_contact = fallback_data.get("contact")
    if not isinstance(fallback_contact, dict):
        fallback_contact = {}

    current_contact = merged.get("contact")
    if not isinstance(current_contact, dict):
        current_contact = {}

    merged_contact = {}
    for field in [
        "email",
        "phone",
        "location",
        "linkedin",
        "github",
        "portfolio",
        "leetcode",
        "codechef",
    ]:
        value = current_contact.get(field) or fallback_contact.get(field)
        if field == "email" and not value:
            value = current_user.email
        if value:
            merged_contact[field] = value
    merged["contact"] = merged_contact

    if not merged.get("summary") and fallback_data.get("summary"):
        merged["summary"] = fallback_data["summary"]

    if not merged.get("skills") and fallback_data.get("skills"):
        merged["skills"] = fallback_data["skills"]
    elif not isinstance(merged.get("skills"), (dict, list)):
        merged["skills"] = fallback_data.get("skills", {})

    for field in ["education", "experience", "projects", "certifications", "achievements"]:
        current_value = merged.get(field)
        fallback_value = fallback_data.get(field)
        if isinstance(current_value, list) and current_value:
            continue
        if isinstance(fallback_value, list) and fallback_value:
            merged[field] = fallback_value
        else:
            merged[field] = current_value if isinstance(current_value, list) else []

    return merged


class RateLimitChecker:
    """Simple in-memory rate limiter. Use Redis in production."""
    
    RESUME_GEN_LIMIT = 10  # Max 10 resumes per hour
    WINDOW_MINUTES = 60
    
    @staticmethod
    def check_limit(user_id: int, action: str) -> tuple[bool, str]:
        """Check if user has exceeded rate limit."""
        cache_key = f"{user_id}:{action}"
        now = datetime.now()
        window_start = now - timedelta(minutes=RateLimitChecker.WINDOW_MINUTES)
        
        if cache_key not in _rate_limit_cache:
            _rate_limit_cache[cache_key] = []
        
        # Clean old timestamps
        _rate_limit_cache[cache_key] = [
            ts for ts in _rate_limit_cache[cache_key]
            if ts > window_start
        ]
        
        if len(_rate_limit_cache[cache_key]) >= RateLimitChecker.RESUME_GEN_LIMIT:
            remaining_wait = int((
                _rate_limit_cache[cache_key][0] + 
                timedelta(minutes=RateLimitChecker.WINDOW_MINUTES) - now
            ).total_seconds())
            message = f"Rate limit exceeded. Try again in {remaining_wait}s"
            logger.warning(f"Rate limit exceeded for user {user_id}: {action}")
            return False, message
        
        # Record this request
        _rate_limit_cache[cache_key].append(now)
        remaining = RateLimitChecker.RESUME_GEN_LIMIT - len(_rate_limit_cache[cache_key])
        return True, f"{remaining} remaining this hour"


class ValidatedResumeGenerateRequest(BaseModel):
    """Validated resume generation request with constraints."""
    job_description: str = Field("", max_length=5000)
    existing_resume: str = Field(None, max_length=50000)  # Increased: full resume JSON can be 15k+ chars
    resume_data: dict = Field(None)
    template_id: int = Field(None)
    additional_context: str = Field(None, max_length=5000)  # Increased from 2000
    
    @validator('job_description')
    def jd_valid(cls, v):
        if not v:
            return ""
        return v.strip()
    
    @validator('existing_resume')
    def existing_resume_valid(cls, v):
        if v and len(v.strip()) < 3:  # Lowered from 5 — allow short inputs too
            return None
        return v.strip() if v else None
    
    @validator('additional_context')
    def context_valid(cls, v):
        if v and len(v.strip()) < 3:
            return None
        return v.strip() if v else None


@router.post("/generate", response_model=ResumeGenerateResponse)
def generate_resume(
    req: ValidatedResumeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new ATS-optimized resume.
    
    This endpoint:
    1. Validates input (JD length, format)
    2. Checks rate limits (max 10/hour)
    3. Calls AI service (Gemini → Groq fallback)
    4. Normalizes output data
    5. Stores in database
    
    Args:
        req: Resume generation request
        current_user: Authenticated user from JWT token
        db: Database session
    
    Returns:
        ResumeGenerateResponse with generated resume and ATS score
    
    Raises:
        HTTPException 400: Invalid input validation
        HTTPException 429: Rate limit exceeded
        HTTPException 500: AI generation or database error
    """
    try:
        # Check rate limit
        allowed, message = RateLimitChecker.check_limit(current_user.id, "resume_generation")
        if not allowed:
            logger.warning(f"Rate limit exceeded for user {current_user.id}")
            raise HTTPException(status_code=429, detail=message)
        
        logger.info(
            f"Resume generation started",
            extra={
                "user_id": current_user.id,
                "jd_length": len(req.job_description),
                "has_existing_resume": bool(req.existing_resume)
            }
        )
        
        # Build context
        context_str = req.existing_resume or ""
        if req.resume_data:
            context_str += "\n\nUser Data Input:\n" + json.dumps(req.resume_data, indent=2)
            
        submitted_resume_data = _parsed_resume_input(req)

        resume = resume_service.generate(
            db=db,
            user_id=current_user.id,
            job_description=req.job_description,
            existing_resume=context_str,
            template_id=req.template_id,
            additional_context=req.additional_context or "",
        )
        
        # --- Normalization Layer ---
        content = json.loads(resume.content) if isinstance(resume.content, str) else resume.content
        if not isinstance(content, dict):
            logger.error(f"Resume content is not dict: {type(content)}")
            content = {"summary": str(content)}

        content = _merge_resume_content(content, submitted_resume_data, current_user)
        resume.content = json.dumps(content)
        resume.raw_text = json.dumps(content, indent=2)
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Log successful generation
        logger.info(
            f"Resume generation successful",
            extra={
                "resume_id": resume.id,
                "user_id": current_user.id,
                "ats_score": resume.ats_score
            }
        )

        return ResumeGenerateResponse(
            id=resume.id,
            title=resume.title,
            content=content,
            raw_text=resume.raw_text or "",
            ats_score=resume.ats_score,
            keywords_matched=json.loads(resume.keywords_matched) if resume.keywords_matched else [],
            keywords_missing=json.loads(resume.keywords_missing) if resume.keywords_missing else [],
            version=resume.version,
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}", extra={"user_id": current_user.id})
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(
            f"Resume generation failed",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {str(e)}")


@router.get("/list", response_model=list[ResumeListItem])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all active resumes for the current user."""
    try:
        resumes = resume_service.list_user_resumes(db, current_user.id)
        logger.debug(f"Listed {len(resumes)} resumes for user {current_user.id}")
        
        return [
            ResumeListItem(
                id=r.id,
                title=r.title,
                ats_score=r.ats_score,
                version=r.version,
                created_at=r.created_at
            )
            for r in resumes
        ]
    except Exception as e:
        logger.error(f"Error listing resumes: {e}", extra={"user_id": current_user.id})
        raise HTTPException(status_code=500, detail="Failed to list resumes")


@router.get("/{resume_id}")
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific resume by ID."""
    try:
        resume = resume_service.get_by_id(db, resume_id, current_user.id)
        if not resume:
            logger.warning(
                f"Resume not found",
                extra={"resume_id": resume_id, "user_id": current_user.id}
            )
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return {
            "id": resume.id,
            "title": resume.title,
            "content": json.loads(resume.content) if isinstance(resume.content, str) else resume.content,
            "raw_text": resume.raw_text,
            "ats_score": resume.ats_score,
            "version": resume.version,
            "created_at": resume.created_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch resume")


@router.get("/{resume_id}/versions")
def get_versions(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get version history for a resume."""
    try:
        # Verify ownership
        resume = resume_service.get_by_id(db, resume_id, current_user.id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        versions = resume_service.get_versions(db, resume_id)
        return [
            {
                "id": v.id,
                "version_number": v.version_number,
                "change_summary": v.change_summary,
                "ats_score": v.ats_score,
                "created_at": v.created_at,
            }
            for v in versions
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching versions for resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch versions")


@router.get("/{resume_id}/download/{format}")
def download_resume(
    resume_id: int,
    format: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download resume in specified format (pdf, docx, txt, html)."""
    try:
        resume = resume_service.get_by_id(db, resume_id, current_user.id)
        if not resume:
            logger.warning(
                f"Attempted download of non-existent resume",
                extra={"resume_id": resume_id, "user_id": current_user.id}
            )
            raise HTTPException(status_code=404, detail="Resume not found")

        content = json.loads(resume.content) if isinstance(resume.content, str) else resume.content

        # Validate format
        valid_formats = ["pdf", "docx", "txt", "html"]
        if format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Use: {', '.join(valid_formats)}"
            )

        logger.info(
            f"Resume download requested",
            extra={"resume_id": resume_id, "user_id": current_user.id, "format": format}
        )

        if format == "pdf":
            html = file_service.render_template(settings.TEMPLATE_NAME, content)
            filepath = file_service.generate_pdf(html)
            if filepath and filepath.endswith(".html"):
                return FileResponse(filepath, filename="resume.html", media_type="text/html")
        elif format == "docx":
            filepath = file_service.generate_docx(content)
        elif format == "txt":
            filepath = file_service.generate_txt(content)
        elif format == "html":
            html = file_service.render_template(settings.TEMPLATE_NAME, content)
            import os, uuid
            html_path = os.path.join(settings.GENERATED_DIR, f"resume_{uuid.uuid4().hex[:8]}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            filepath = html_path

        if not filepath:
            logger.error(f"File generation failed for resume {resume_id}")
            raise HTTPException(status_code=500, detail="File generation failed")

        # Determine proper media type and filename
        media_type_map = {
            "pdf": ("application/pdf", "resume.pdf"),
            "html": ("text/html", "resume.html"),
            "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "resume.docx"),
            "txt": ("text/plain", "resume.txt"),
        }
        
        media_type, dl_name = media_type_map.get(format, ("application/octet-stream", f"resume.{format}"))

        logger.info(
            f"Resume downloaded successfully",
            extra={"resume_id": resume_id, "user_id": current_user.id, "format": format}
        )

        return FileResponse(filepath, filename=dl_name, media_type=media_type)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Download failed")


@router.delete("/{resume_id}")
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete (soft delete) a resume."""
    try:
        if resume_service.delete(db, resume_id, current_user.id):
            logger.info(
                f"Resume deleted",
                extra={"resume_id": resume_id, "user_id": current_user.id}
            )
            return {"message": "Resume deleted"}
        
        logger.warning(
            f"Resume not found for deletion",
            extra={"resume_id": resume_id, "user_id": current_user.id}
        )
        raise HTTPException(status_code=404, detail="Resume not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Deletion failed")
