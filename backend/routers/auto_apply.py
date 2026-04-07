"""
Auto Job Apply Agent — FastAPI Router
Endpoints for AI-powered job application automation.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.routers.auth import get_current_user
from backend.models.user import User
from backend.services.auto_apply_service import (
    parse_job_description,
    generate_application_answers,
    compute_skill_match,
    run_playwright_apply,
    PLAYWRIGHT_AVAILABLE,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auto-apply", tags=["auto-apply"])


# ─── Request/Response Models ──────────────────────────────────────────────────

class ParseJDRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    resume_skills: Optional[list] = []


class GenerateAnswersRequest(BaseModel):
    jd_data: dict
    resume_content: dict
    user_profile: Optional[dict] = {}


class SubmitApplicationRequest(BaseModel):
    jd_data: dict
    answers: dict
    resume_path: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/status")
def agent_status():
    """Check Auto Apply Agent capabilities."""
    return {
        "agent": "Auto Job Apply Agent",
        "version": "1.0.0",
        "ai_prep_mode": True,
        "browser_auto_mode": PLAYWRIGHT_AVAILABLE,
        "playwright_installed": PLAYWRIGHT_AVAILABLE,
        "supported_platforms": ["LinkedIn", "Naukri", "Indeed", "Company Websites", "AngelList"],
        "features": [
            "JD parsing & field extraction",
            "AI-powered answer generation",
            "Skill match scoring",
            "Application form pre-fill",
            "Job tracker integration",
            *(["Playwright browser automation"] if PLAYWRIGHT_AVAILABLE else []),
        ],
    }


@router.post("/parse-jd")
def parse_jd(
    request: ParseJDRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Step 1: Parse a job description (text or URL).
    Returns structured JD data: company, role, skills, required fields, apply URL, etc.
    Also computes a skill match score against the user's resume skills.
    """
    if not request.text and not request.url:
        raise HTTPException(status_code=400, detail="Provide either 'text' (JD content) or 'url' (job posting URL)")

    logger.info(f"User {current_user.id} parsing JD — URL={request.url or 'N/A'}")

    jd_data = parse_job_description(text=request.text, url=request.url)

    if jd_data.get("error"):
        raise HTTPException(status_code=422, detail=jd_data["error"])

    # Compute skill match if resume skills provided
    match_data = {}
    if request.resume_skills:
        match_data = compute_skill_match(
            resume_skills=request.resume_skills,
            jd_required=jd_data.get("required_skills", []),
            jd_preferred=jd_data.get("preferred_skills", []),
        )

    return {
        "jd_data": jd_data,
        "skill_match": match_data,
        "parser_confidence": "high" if jd_data.get("company") != "Unknown Company" else "medium",
    }


@router.post("/generate-answers")
def generate_answers(
    request: GenerateAnswersRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Step 2: Generate AI-powered, personalized answers for every application field.
    Takes parsed JD data + resume content and produces ready-to-use answers.
    """
    logger.info(
        f"User {current_user.id} generating answers for: "
        f"{request.jd_data.get('company', 'Unknown')} — {request.jd_data.get('role', 'Unknown')}"
    )

    # Merge user_profile from request with current_user data
    user_profile = {
        "full_name": current_user.full_name or "",
        "email": current_user.email or "",
        "phone": current_user.phone or "",
        "linkedin": current_user.linkedin_url or "",
        "github": current_user.github_username or "",
        "experience_years": current_user.experience_years or 0,
    }
    # Allow request to override profile fields
    user_profile.update(request.user_profile or {})

    answers = generate_application_answers(
        jd_data=request.jd_data,
        user_profile=user_profile,
        resume_content=request.resume_content,
    )

    return {
        "answers": answers,
        "total_fields": len(answers),
        "ai_generated": True,
        "editable": True,
        "note": "All answers are AI-generated. Review and edit before submitting."
    }


@router.post("/submit")
def submit_application(
    request: SubmitApplicationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Step 3: Submit the application.
    - If Playwright is available (local): Opens browser, fills and submits form
    - If not (hosted): Returns 'AI Prep' mode with copy-ready answers
    """
    apply_url = request.jd_data.get("apply_url")
    company = request.jd_data.get("company", "Unknown")
    role = request.jd_data.get("role", "Unknown")

    logger.info(f"User {current_user.id} submitting application to {company} for {role}")

    result = run_playwright_apply(
        jd_data=request.jd_data,
        answers=request.answers,
        resume_path=request.resume_path,
    )

    return {
        "submission_result": result,
        "company": company,
        "role": role,
        "apply_url": apply_url,
        "mode": result.get("mode", "ai_prep"),
        "tracker_note": "Application has been tracked in your Job Tracker.",
    }
