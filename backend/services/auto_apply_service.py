"""
Auto Job Apply Agent Service
Handles JD parsing, AI answer generation, and optional Playwright form submission.
"""
import logging
import re
from typing import Optional

import requests as http_requests

from backend.ai.chains import parse_jd_for_apply, generate_apply_answers

logger = logging.getLogger(__name__)

# ─── Playwright availability check ───────────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.info("Playwright not installed — AI prep mode only")


# ─── JD Text extraction from URL ─────────────────────────────────────────────

def _fetch_url_text(url: str) -> str:
    """Fetch and extract plain text from a URL (best-effort)."""
    try:
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = http_requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:6000]
    except Exception as e:
        logger.warning(f"Failed to fetch URL {url}: {e}")
        return f"URL: {url}\n[Could not fetch content automatically. Please paste the JD text manually.]"


# ─── Step 1: Parse JD ────────────────────────────────────────────────────────

def parse_job_description(text: str = None, url: str = None) -> dict:
    """
    Parse a job description (from raw text or URL) into structured data.
    Returns company, role, skills, apply_url, form fields, etc.
    """
    if url and not text:
        logger.info(f"Fetching JD from URL: {url}")
        text = _fetch_url_text(url)
    elif not text:
        return {"error": "No JD text or URL provided"}

    result = parse_jd_for_apply(text)

    if result.get("error"):
        return result

    # Normalize — ensure all required fields exist
    result.setdefault("company", "Unknown Company")
    result.setdefault("role", "Unknown Role")
    result.setdefault("required_skills", [])
    result.setdefault("preferred_skills", [])
    result.setdefault("application_fields", _default_fields())
    result.setdefault("responsibilities", [])
    result.setdefault("key_highlights", [])
    result.setdefault("apply_url", None)
    result.setdefault("apply_platform", "Other")
    result.setdefault("experience_required", "Not specified")
    result.setdefault("job_type", "Full-time")
    result.setdefault("location", "Not specified")

    # Inject original URL if apply_url is missing
    if not result.get("apply_url") and url:
        result["apply_url"] = url

    return result


def _default_fields() -> list:
    return [
        {"field": "full_name",        "label": "Full Name",           "type": "text",     "required": True},
        {"field": "email",            "label": "Email Address",       "type": "email",    "required": True},
        {"field": "phone",            "label": "Phone Number",        "type": "text",     "required": True},
        {"field": "linkedin",         "label": "LinkedIn Profile",    "type": "url",      "required": False},
        {"field": "cover_note",       "label": "Cover Note",          "type": "textarea", "required": True},
        {"field": "experience_years", "label": "Years of Experience", "type": "number",   "required": True},
        {"field": "expected_salary",  "label": "Expected CTC (LPA)",  "type": "text",     "required": False},
        {"field": "notice_period",    "label": "Notice Period",       "type": "text",     "required": False},
        {"field": "why_company",      "label": "Why join us?",        "type": "textarea", "required": False},
        {"field": "portfolio",        "label": "Portfolio / GitHub",  "type": "url",      "required": False},
        {"field": "resume",           "label": "Resume Upload",       "type": "file",     "required": True},
    ]


# ─── Skill Match ─────────────────────────────────────────────────────────────

def compute_skill_match(resume_skills: list, jd_required: list, jd_preferred: list) -> dict:
    """Compare resume skills against JD requirements."""
    def _normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9+#.]", "", s.lower())

    resume_norm = {_normalize(s) for s in resume_skills}
    matched_required = [s for s in jd_required if _normalize(s) in resume_norm]
    missing_required = [s for s in jd_required if _normalize(s) not in resume_norm]
    matched_preferred = [s for s in jd_preferred if _normalize(s) in resume_norm]

    total = len(jd_required) + len(jd_preferred)
    matched = len(matched_required) + len(matched_preferred)
    score = int((matched / total) * 100) if total > 0 else 50

    return {
        "match_score": score,
        "matched_required": matched_required,
        "missing_required": missing_required,
        "matched_preferred": matched_preferred,
    }


# ─── Generate Application Answers ────────────────────────────────────────────

def generate_application_answers(jd_data: dict, user_profile: dict, resume_content: dict) -> dict:
    """Generate AI-powered, personalized answers for each application field."""
    # Build resume summary for the prompt
    resume_summary_parts = []

    summary = resume_content.get("summary", "")
    if summary:
        resume_summary_parts.append(f"Summary: {summary}")

    skills = resume_content.get("skills", {})
    if isinstance(skills, dict):
        skills_str = " | ".join(f"{k}: {v}" for k, v in list(skills.items())[:4])
        resume_summary_parts.append(f"Skills: {skills_str}")
    elif isinstance(skills, list):
        resume_summary_parts.append(f"Skills: {', '.join(skills[:15])}")

    experience = resume_content.get("experience", [])
    if experience:
        exp_parts = []
        for exp in experience[:3]:
            if isinstance(exp, dict):
                exp_parts.append(f"{exp.get('title', '')} at {exp.get('company', '')} ({exp.get('dates', '')})")
        if exp_parts:
            resume_summary_parts.append("Experience: " + " | ".join(exp_parts))

    projects = resume_content.get("projects", [])
    if projects:
        proj_names = [p.get("name", "") for p in projects[:3] if isinstance(p, dict)]
        resume_summary_parts.append(f"Projects: {', '.join(filter(None, proj_names))}")

    resume_summary = "\n".join(resume_summary_parts) or "Experienced developer with strong technical skills."

    required_skills = jd_data.get("required_skills", [])
    responsibilities = jd_data.get("responsibilities", [])
    requirements_str = ", ".join(required_skills[:8])
    if responsibilities:
        requirements_str += " | " + "; ".join(responsibilities[:3])

    full_name = user_profile.get("full_name", "")
    email = user_profile.get("email", "")
    phone = user_profile.get("phone", "")
    linkedin = user_profile.get("linkedin", "")
    github = user_profile.get("github", "")
    experience_years = str(user_profile.get("experience_years", 0))

    answers = generate_apply_answers(
        company=jd_data.get("company", "the company"),
        role=jd_data.get("role", "the role"),
        requirements=requirements_str,
        resume_summary=resume_summary,
        full_name=full_name,
        email=email,
        phone=phone,
        linkedin=linkedin,
        github=github,
        experience_years=experience_years,
    )

    if answers.get("error"):
        logger.warning(f"Answer generation AI failed, using fallback")
        return _fallback_answers(user_profile, jd_data)

    # Ensure contact info from actual profile (not AI hallucination)
    answers["full_name"] = full_name or answers.get("full_name", "")
    answers["email"] = email or answers.get("email", "")
    answers["phone"] = phone or answers.get("phone", "")
    answers["linkedin"] = linkedin or answers.get("linkedin", "")
    answers["portfolio"] = github or answers.get("portfolio", "")

    return answers


def _fallback_answers(user_profile: dict, jd_data: dict) -> dict:
    company = jd_data.get("company", "your company")
    role = jd_data.get("role", "this role")
    return {
        "full_name": user_profile.get("full_name", ""),
        "email": user_profile.get("email", ""),
        "phone": user_profile.get("phone", ""),
        "linkedin": user_profile.get("linkedin", ""),
        "portfolio": user_profile.get("github", ""),
        "experience_years": str(user_profile.get("experience_years", 0)),
        "current_salary": "",
        "expected_salary": "",
        "notice_period": "30 days",
        "cover_note": (
            f"I am excited to apply for the {role} position at {company}. "
            "My experience and skills align well with your requirements. "
            "I look forward to contributing to your team."
        ),
        "why_company": (
            f"I am drawn to {company}'s innovative approach and strong market presence. "
            "I believe this role offers an excellent opportunity for mutual growth."
        ),
        "headline": f"Developer | {role}",
        "availability": "Immediately available",
        "referral": "",
        "additional_info": "",
    }


# ─── Playwright Auto-Submit (Local Only) ─────────────────────────────────────

def run_playwright_apply(jd_data: dict, answers: dict, resume_path: str = None) -> dict:
    """
    Use Playwright to auto-fill a job application form.
    Only works locally. Gracefully degrades to AI Prep mode.
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {
            "success": False,
            "mode": "ai_prep",
            "message": (
                "Running in AI Prep Mode — Your personalized application package is ready! "
                "Copy and paste the AI-generated answers to apply on the platform."
            ),
        }

    apply_url = jd_data.get("apply_url")
    if not apply_url:
        return {
            "success": False,
            "mode": "ai_prep",
            "message": "No direct apply URL found. Use the AI-generated answers to apply on the platform.",
        }

    try:
        return _playwright_fill_form(apply_url, answers, resume_path)
    except Exception as e:
        logger.error(f"Playwright error: {e}", exc_info=True)
        return {
            "success": False,
            "mode": "ai_prep",
            "message": f"Browser automation hit an issue: {str(e)[:200]}. Your AI answers are ready.",
        }


def _playwright_fill_form(url: str, answers: dict, resume_path: str = None) -> dict:
    """Internal Playwright form-fill logic."""
    import base64

    FIELD_SELECTORS = {
        "full_name": ["input[name*='name' i]", "input[placeholder*='name' i]", "input[id*='name' i]"],
        "email": ["input[type='email']", "input[name*='email' i]", "input[placeholder*='email' i]"],
        "phone": ["input[type='tel']", "input[name*='phone' i]", "input[name*='mobile' i]"],
        "linkedin": ["input[name*='linkedin' i]", "input[placeholder*='linkedin' i]"],
        "cover_note": [
            "textarea[name*='cover' i]", "textarea[placeholder*='cover' i]",
            "textarea[name*='message' i]", "textarea:first-of-type"
        ],
        "portfolio": ["input[name*='portfolio' i]", "input[name*='github' i]"],
        "experience_years": ["input[name*='experience' i]", "input[name*='years' i]"],
        "expected_salary": ["input[name*='salary' i]", "input[name*='ctc' i]", "input[name*='compensation' i]"],
        "notice_period": ["input[name*='notice' i]", "select[name*='notice' i]"],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        try:
            page.goto(url, wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(2000)

            filled_fields = []
            for field_key, selectors in FIELD_SELECTORS.items():
                value = answers.get(field_key, "")
                if not value:
                    continue
                for selector in selectors:
                    try:
                        el = page.query_selector(selector)
                        if el and el.is_visible():
                            tag = el.evaluate("el => el.tagName.toLowerCase()")
                            if tag == "select":
                                el.select_option(label=value)
                            else:
                                el.fill(str(value))
                            filled_fields.append(field_key)
                            break
                    except Exception:
                        continue

            if resume_path:
                for sel in ["input[type='file']", "input[name*='resume' i]", "input[accept*='.pdf' i]"]:
                    try:
                        el = page.query_selector(sel)
                        if el:
                            el.set_input_files(resume_path)
                            filled_fields.append("resume")
                            break
                    except Exception:
                        continue

            ss_bytes = page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(ss_bytes).decode("utf-8")
            browser.close()

            return {
                "success": True,
                "mode": "auto",
                "message": (
                    f"🤖 Browser agent filled {len(filled_fields)} fields! "
                    f"({', '.join(filled_fields)}) — Review and click Submit."
                ),
                "filled_fields": filled_fields,
                "screenshot_base64": screenshot_b64,
                "apply_url": url,
            }

        except Exception as e:
            try:
                browser.close()
            except Exception:
                pass
            raise e
