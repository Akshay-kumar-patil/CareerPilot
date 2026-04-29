"""Resume generation and management API routes — MongoDB-primary."""
import json
import logging
import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from backend.models.user import user_doc_to_response
from backend.schemas.resume import ResumeGenerateRequest, ResumeGenerateResponse, ResumeListItem
from backend.utils.auth import get_current_user
from backend.utils.helpers import calculate_keyword_match
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


def _as_list(value):
    return value if isinstance(value, list) else []


def _as_text(value) -> str:
    if isinstance(value, list):
        value = " ".join(str(item).strip() for item in value if str(item).strip())
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        cleaned = re.sub(r"\s+", " ", str(item or "")).strip(" -\t\r\n")
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def _trim_summary(summary, fallback_summary="") -> str:
    text = _as_text(summary) or _as_text(fallback_summary)
    if not text:
        return ""

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        sentences = [text]

    trimmed = " ".join(sentences[:3]).strip()
    words = trimmed.split()
    if len(words) > 55:
        trimmed = " ".join(words[:55]).rstrip(",;:")
        if trimmed and trimmed[-1] not in ".!?":
            trimmed += "."
    return trimmed


def _merge_bullets(ai_bullets, fallback_bullets, max_count: int) -> list[str]:
    merged = _dedupe_keep_order(_as_list(ai_bullets) + _as_list(fallback_bullets))
    return merged[:max_count]


def _normalize_experience(ai_experience, fallback_experience) -> list[dict]:
    ai_experience = _as_list(ai_experience)
    fallback_experience = _as_list(fallback_experience)
    total = len(fallback_experience) if fallback_experience else len(ai_experience)
    result = []

    for idx in range(total):
        ai_item = ai_experience[idx] if idx < len(ai_experience) and isinstance(ai_experience[idx], dict) else {}
        fallback_item = fallback_experience[idx] if idx < len(fallback_experience) and isinstance(fallback_experience[idx], dict) else {}
        item = {
            "title": ai_item.get("title") or fallback_item.get("title") or "",
            "company": ai_item.get("company") or fallback_item.get("company") or "",
            "location": ai_item.get("location") or fallback_item.get("location") or "",
            "dates": ai_item.get("dates") or fallback_item.get("dates") or "",
            "bullets": _merge_bullets(ai_item.get("bullets"), fallback_item.get("bullets"), 4),
        }
        if item["title"] or item["company"] or item["bullets"]:
            result.append(item)

    return result


def _normalize_projects(ai_projects, fallback_projects, has_experience: bool) -> list[dict]:
    ai_projects = _as_list(ai_projects)
    fallback_projects = _as_list(fallback_projects)
    total = len(fallback_projects) if fallback_projects else len(ai_projects)
    max_bullets = 2 if has_experience else 3
    result = []

    for idx in range(total):
        ai_item = ai_projects[idx] if idx < len(ai_projects) and isinstance(ai_projects[idx], dict) else {}
        fallback_item = fallback_projects[idx] if idx < len(fallback_projects) and isinstance(fallback_projects[idx], dict) else {}
        item = {
            "name": ai_item.get("name") or fallback_item.get("name") or "",
            "tech_stack": ai_item.get("tech_stack") or fallback_item.get("tech_stack") or "",
            "live_url": ai_item.get("live_url") or fallback_item.get("live_url") or "",
            "repo_url": ai_item.get("repo_url") or fallback_item.get("repo_url") or "",
            "bullets": _merge_bullets(ai_item.get("bullets"), fallback_item.get("bullets"), max_bullets),
        }
        if item["name"] or item["bullets"]:
            result.append(item)

    return result


def _finalize_resume_content(content: dict, fallback_data: dict, current_user: dict) -> dict:
    merged = _merge_resume_content(content, fallback_data, current_user)
    fallback_data = fallback_data or {}

    has_experience = bool(_as_list(fallback_data.get("experience")) or _as_list(merged.get("experience")))
    merged["summary"] = _trim_summary(merged.get("summary"), fallback_data.get("summary"))
    merged["experience"] = _normalize_experience(merged.get("experience"), fallback_data.get("experience"))
    merged["projects"] = _normalize_projects(merged.get("projects"), fallback_data.get("projects"), has_experience)
    merged["education"] = _as_list(merged.get("education"))
    merged["certifications"] = _as_list(merged.get("certifications"))
    merged["achievements"] = _dedupe_keep_order(_as_list(merged.get("achievements")))

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

from fastapi import BackgroundTasks
import uuid

# In-memory store for long-running AI jobs (bypasses Render 100s timeout)
_job_store = {}

@router.post("/generate", response_model=dict)
def generate_resume_start(
    req: ValidatedResumeGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Start resume generation in the background to avoid proxy timeout."""
    user_id = current_user["id"]
    allowed, message = RateLimitChecker.check_limit(user_id, "resume_generation")
    if not allowed:
        raise HTTPException(status_code=429, detail=message)

    job_id = str(uuid.uuid4())
    _job_store[job_id] = {"status": "processing", "result": None, "error": None}

    def _do_background_generation(j_id: str, u_id: str, request_obj: ValidatedResumeGenerateRequest, c_user: dict):
        try:
            context_str = request_obj.existing_resume or ""
            if request_obj.resume_data:
                context_str += "\n\nUser Data Input:\n" + json.dumps(request_obj.resume_data, indent=2)

            submitted_resume_data = _parsed_resume_input(request_obj)

            resume = resume_service.generate(
                user_id=u_id,
                job_description=request_obj.job_description,
                existing_resume=context_str,
                template_id=request_obj.template_id,
                additional_context=request_obj.additional_context or "",
            )

            content = resume.get("content", {})
            if not isinstance(content, dict):
                try:
                    content = json.loads(content)
                except Exception:
                    content = {"summary": str(content)}

            content = _finalize_resume_content(content, submitted_resume_data, c_user)
            kw_analysis = calculate_keyword_match(
                json.dumps(content, indent=2),
                request_obj.job_description or "",
            )

            # Persist merged content back
            from backend.database import get_resumes_collection
            from bson import ObjectId
            get_resumes_collection().update_one(
                {"_id": ObjectId(resume["id"])},
                {"$set": {
                    "content": content,
                    "raw_text": json.dumps(content, indent=2),
                    "ats_score": kw_analysis["score"],
                    "keywords_matched": kw_analysis["matched"],
                    "keywords_missing": kw_analysis["missing"],
                }},
            )

            result_obj = ResumeGenerateResponse(
                id=resume["id"],
                title=resume["title"],
                content=content,
                raw_text=json.dumps(content, indent=2),
                ats_score=kw_analysis["score"],
                keywords_matched=kw_analysis["matched"],
                keywords_missing=kw_analysis["missing"],
                version=resume.get("version", 1),
            )
            _job_store[j_id]["status"] = "completed"
            _job_store[j_id]["result"] = result_obj.dict()

        except Exception as e:
            logger.error(f"Background resume generation failed: {e}", exc_info=True)
            _job_store[j_id]["status"] = "failed"
            _job_store[j_id]["error"] = str(e)

    background_tasks.add_task(_do_background_generation, job_id, user_id, req, current_user)
    return {"job_id": job_id, "status": "processing"}

@router.get("/generate/status/{job_id}", response_model=dict)
def get_generation_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """Check the status of a background resume generation job."""
    job = _job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


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
