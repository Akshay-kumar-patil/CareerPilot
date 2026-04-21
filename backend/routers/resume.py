"""Resume generation and management API routes — MongoDB-primary."""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from backend.models.user import user_doc_to_response
from backend.schemas.resume import ResumeGenerateRequest, ResumeGenerateResponse, ResumeListItem
from backend.utils.auth import get_current_user
from backend.services.resume_service import resume_service
from backend.services.file_service import file_service
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resume", tags=["Resume"])

# Rate limiting — simple in-memory per user per action
_rate_limit_cache = {}

_PLACEHOLDER_NAMES = {"your name", "first last", "full name", "name"}


def _parsed_resume_input(req) -> dict:
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
    if not value:
        return True
    return value.strip().lower() in _PLACEHOLDER_NAMES


def _merge_resume_content(content: dict, fallback_data: dict, current_user: dict) -> dict:
    """Merge AI output with submitted form data so previews/downloads stay populated."""
    merged = dict(content) if isinstance(content, dict) else {}
    fallback_data = fallback_data or {}

    if _is_placeholder_name(merged.get("full_name")):
        merged["full_name"] = (
            fallback_data.get("full_name")
            or current_user.get("full_name")
            or merged.get("full_name")
            or "Your Name"
        )

    fallback_contact = fallback_data.get("contact") or {}
    current_contact = merged.get("contact") or {}
    if not isinstance(fallback_contact, dict):
        fallback_contact = {}
    if not isinstance(current_contact, dict):
        current_contact = {}

    merged_contact = {}
    for field in ["email", "phone", "location", "linkedin", "github", "portfolio", "leetcode", "codechef"]:
        value = current_contact.get(field) or fallback_contact.get(field)
        if field == "email" and not value:
            value = current_user.get("email")
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
    RESUME_GEN_LIMIT = 10
    WINDOW_MINUTES = 60

    @staticmethod
    def check_limit(user_id: str, action: str) -> tuple[bool, str]:
        cache_key = f"{user_id}:{action}"
        now = datetime.now()
        window_start = now - timedelta(minutes=RateLimitChecker.WINDOW_MINUTES)

        if cache_key not in _rate_limit_cache:
            _rate_limit_cache[cache_key] = []

        _rate_limit_cache[cache_key] = [
            ts for ts in _rate_limit_cache[cache_key] if ts > window_start
        ]

        if len(_rate_limit_cache[cache_key]) >= RateLimitChecker.RESUME_GEN_LIMIT:
            wait = int((
                _rate_limit_cache[cache_key][0]
                + timedelta(minutes=RateLimitChecker.WINDOW_MINUTES)
                - now
            ).total_seconds())
            return False, f"Rate limit exceeded. Try again in {wait}s"

        _rate_limit_cache[cache_key].append(now)
        remaining = RateLimitChecker.RESUME_GEN_LIMIT - len(_rate_limit_cache[cache_key])
        return True, f"{remaining} remaining this hour"


class ValidatedResumeGenerateRequest(BaseModel):
    job_description: str = Field("", max_length=5000)
    existing_resume: str = Field(None, max_length=50000)
    resume_data: dict = Field(None)
    template_id: int = Field(None)
    additional_context: str = Field(None, max_length=5000)

    @validator("job_description")
    def jd_valid(cls, v):
        return v.strip() if v else ""

    @validator("existing_resume")
    def existing_resume_valid(cls, v):
        if v and len(v.strip()) < 3:
            return None
        return v.strip() if v else None

    @validator("additional_context")
    def context_valid(cls, v):
        if v and len(v.strip()) < 3:
            return None
        return v.strip() if v else None


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=ResumeGenerateResponse)
def generate_resume(
    req: ValidatedResumeGenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = current_user["id"]

        allowed, message = RateLimitChecker.check_limit(user_id, "resume_generation")
        if not allowed:
            raise HTTPException(status_code=429, detail=message)

        context_str = req.existing_resume or ""
        if req.resume_data:
            context_str += "\n\nUser Data Input:\n" + json.dumps(req.resume_data, indent=2)

        submitted_resume_data = _parsed_resume_input(req)

        resume = resume_service.generate(
            user_id=user_id,
            job_description=req.job_description,
            existing_resume=context_str,
            template_id=req.template_id,
            additional_context=req.additional_context or "",
        )

        content = resume.get("content", {})
        if not isinstance(content, dict):
            try:
                content = json.loads(content)
            except Exception:
                content = {"summary": str(content)}

        content = _merge_resume_content(content, submitted_resume_data, current_user)

        # Persist merged content back
        from backend.database import get_resumes_collection
        from bson import ObjectId
        get_resumes_collection().update_one(
            {"_id": ObjectId(resume["id"])},
            {"$set": {"content": content, "raw_text": json.dumps(content, indent=2)}},
        )

        return ResumeGenerateResponse(
            id=resume["id"],
            title=resume["title"],
            content=content,
            raw_text=json.dumps(content, indent=2),
            ats_score=resume.get("ats_score"),
            keywords_matched=resume.get("keywords_matched") or [],
            keywords_missing=resume.get("keywords_missing") or [],
            version=resume.get("version", 1),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error("Resume generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {e}")


@router.get("/list", response_model=list[ResumeListItem])
def list_resumes(current_user: dict = Depends(get_current_user)):
    try:
        resumes = resume_service.list_user_resumes(current_user["id"])
        return [
            ResumeListItem(
                id=r["id"],
                title=r["title"],
                ats_score=r.get("ats_score"),
                version=r.get("version", 1),
                created_at=r.get("created_at"),
            )
            for r in resumes
        ]
    except Exception as e:
        logger.error("Error listing resumes: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list resumes")


@router.get("/{resume_id}")
def get_resume(resume_id: str, current_user: dict = Depends(get_current_user)):
    try:
        resume = resume_service.get_by_id(resume_id, current_user["id"])
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        return {
            "id": resume["id"],
            "title": resume["title"],
            "content": resume.get("content", {}),
            "raw_text": resume.get("raw_text", ""),
            "ats_score": resume.get("ats_score"),
            "version": resume.get("version", 1),
            "created_at": resume.get("created_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching resume %s: %s", resume_id, e)
        raise HTTPException(status_code=500, detail="Failed to fetch resume")


@router.get("/{resume_id}/versions")
def get_versions(resume_id: str, current_user: dict = Depends(get_current_user)):
    try:
        resume = resume_service.get_by_id(resume_id, current_user["id"])
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        return resume_service.get_versions(resume_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching versions for resume %s: %s", resume_id, e)
        raise HTTPException(status_code=500, detail="Failed to fetch versions")


@router.get("/{resume_id}/download/{format}")
def download_resume(
    resume_id: str,
    format: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        resume = resume_service.get_by_id(resume_id, current_user["id"])
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        content = resume.get("content", {})
        if isinstance(content, str):
            content = json.loads(content)

        valid_formats = ["pdf", "docx", "txt", "html"]
        if format not in valid_formats:
            raise HTTPException(status_code=400, detail=f"Invalid format. Use: {', '.join(valid_formats)}")

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
            raise HTTPException(status_code=500, detail="File generation failed")

        media_type_map = {
            "pdf": ("application/pdf", "resume.pdf"),
            "html": ("text/html", "resume.html"),
            "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "resume.docx"),
            "txt": ("text/plain", "resume.txt"),
        }
        media_type, dl_name = media_type_map.get(format, ("application/octet-stream", f"resume.{format}"))
        return FileResponse(filepath, filename=dl_name, media_type=media_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error downloading resume %s: %s", resume_id, e)
        raise HTTPException(status_code=500, detail="Download failed")


@router.delete("/{resume_id}")
def delete_resume(resume_id: str, current_user: dict = Depends(get_current_user)):
    try:
        if resume_service.delete(resume_id, current_user["id"]):
            return {"message": "Resume deleted"}
        raise HTTPException(status_code=404, detail="Resume not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting resume %s: %s", resume_id, e)
        raise HTTPException(status_code=500, detail="Deletion failed")
