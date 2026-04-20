"""
API client for Streamlit frontend to communicate with FastAPI backend.
"""
import os
import requests
import streamlit as st
from typing import Optional
from dotenv import load_dotenv

# Load .env file from the root directory with override so local .env takes precedence
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"), override=True)

BASE_URL = os.environ.get("API_BASE_URL", "https://career-portal-cxgd.onrender.com").rstrip("/")

# FIX #9: Define standard timeouts as constants so they're consistent everywhere
_TIMEOUT_SHORT = 10    # for simple read/write operations
_TIMEOUT_AI = 300      # for AI generation calls (Render free-tier + LLM can take 3-5 min)


def _headers() -> dict:
    """Get auth headers from session state."""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _handle_response(resp: requests.Response) -> Optional[dict]:
    """Handle API response, showing errors in Streamlit."""
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 401:
        st.session_state.pop("token", None)
        st.session_state.pop("user", None)
        st.error("Session expired. Please log in again.")
        return None
    else:
        try:
            js = resp.json()
            if isinstance(js, dict):
                detail = js.get("detail", str(js))
            else:
                detail = str(js)
        except Exception:
            detail = resp.text
            
        if not detail or detail.isspace():
            detail = f"Empty response body (HTTP {resp.status_code})"
            
        st.error(f"API Error ({resp.status_code}): {detail}")
        return None


# --- Auth ---
def register(email: str, password: str, full_name: str) -> Optional[dict]:
    resp = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
        timeout=_TIMEOUT_SHORT,
    )
    return _handle_response(resp)


def google_oauth_status():
    """Check whether Google OAuth is configured on the backend."""
    try:
        resp = requests.get(f"{BASE_URL}/api/auth/google/status", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def get_google_login_url():
    """Return the backend URL that starts the Google OAuth flow."""
    return f"{BASE_URL}/api/auth/google"


def login(email: str, password: str) -> Optional[dict]:
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=_TIMEOUT_SHORT,
    )
    return _handle_response(resp)


def get_me() -> Optional[dict]:
    resp = requests.get(f"{BASE_URL}/api/auth/me", headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


def update_profile(data: dict) -> Optional[dict]:
    resp = requests.put(f"{BASE_URL}/api/auth/profile", json=data, headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


# --- AI Status ---
def get_ai_status() -> Optional[dict]:
    try:
        resp = requests.get(f"{BASE_URL}/api/ai/status", timeout=3)
        return resp.json()
    except Exception:
        return None


# --- Resume ---
def generate_resume(
    job_description: str,
    existing_resume: str = "",
    template_id: int = None,
    additional_context: str = "",
    resume_data: dict = None,
) -> Optional[dict]:
    payload = {
        "job_description": job_description,
        "existing_resume": existing_resume,
        "additional_context": additional_context,
    }
    if resume_data:
        payload["resume_data"] = resume_data
    if template_id:
        payload["template_id"] = template_id
    resp = requests.post(
        f"{BASE_URL}/api/resume/generate",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT_AI,
    )
    return _handle_response(resp)

def preview_resume(resume_id: int) -> str:
    resp = requests.get(
        f"{BASE_URL}/api/resume/{resume_id}/preview",
        headers=_headers(),
        timeout=20
    )
    if resp.status_code == 200:
        return resp.text
    return ""

def list_resumes() -> Optional[list]:
    resp = requests.get(f"{BASE_URL}/api/resume/list", headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


def get_resume(resume_id: int) -> Optional[dict]:
    resp = requests.get(f"{BASE_URL}/api/resume/{resume_id}", headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


def download_resume(resume_id: int, fmt: str) -> Optional[bytes]:
    # FIX #1: Changed from requests.post to requests.get — backend uses GET for downloads
    resp = requests.get(
        f"{BASE_URL}/api/resume/{resume_id}/download/{fmt}",
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.content
    return None


def delete_resume(resume_id: int) -> bool:
    resp = requests.delete(
        f"{BASE_URL}/api/resume/{resume_id}",
        headers=_headers(),
        timeout=_TIMEOUT_SHORT,
    )
    return resp.status_code == 200


# --- Analyzer ---
def analyze_resume(resume_text: str, job_description: str = "") -> Optional[dict]:
    resp = requests.post(
        f"{BASE_URL}/api/analyzer/analyze",
        json={"resume_text": resume_text, "job_description": job_description},
        headers=_headers(),
        timeout=_TIMEOUT_AI,
    )
    return _handle_response(resp)


def upload_resume_file(file_bytes: bytes, filename: str, content_type: str) -> Optional[dict]:
    """Upload a resume file and get extracted text + analysis back."""
    resp = requests.post(
        f"{BASE_URL}/api/analyzer/upload",
        files={"file": (filename, file_bytes, content_type)},
        headers=_headers(),
        timeout=_TIMEOUT_AI,
    )
    return _handle_response(resp)


def quick_score(resume_text: str, job_description: str) -> Optional[dict]:
    resp = requests.post(
        f"{BASE_URL}/api/analyzer/quick-score",
        json={"resume_text": resume_text, "job_description": job_description},
        headers=_headers(),
        timeout=_TIMEOUT_SHORT,
    )
    return _handle_response(resp)


# --- Cover Letter ---
def generate_cover_letter(
    company: str,
    role: str,
    jd: str = "",
    skills: list = None,
    tone: str = "formal",
    context: str = "",
) -> Optional[dict]:
    payload = {
        "company_name": company,
        "role": role,
        "job_description": jd,
        "key_skills": skills or [],
        "tone": tone,
        "additional_context": context,
    }
    resp = requests.post(
        f"{BASE_URL}/api/cover-letter/generate",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT_AI,
    )
    return _handle_response(resp)

print("--- api_client.py loaded ---")

def download_cover_letter(content: dict, fmt: str) -> Optional[bytes]:
    """Download a cover letter in a specific format."""
    resp = requests.post(
        f"{BASE_URL}/api/cover-letter/download/{fmt}",
        json={"content": content},
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.content
    return None


# --- Applications ---
def create_application(data: dict) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/applications/", json=data, headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


def list_applications(status: str = None) -> Optional[list]:
    params = {"status": status} if status else {}
    resp = requests.get(f"{BASE_URL}/api/applications/", params=params, headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


def update_application(app_id: int, data: dict) -> Optional[dict]:
    resp = requests.put(f"{BASE_URL}/api/applications/{app_id}", json=data, headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


def delete_application(app_id: int) -> Optional[dict]:
    resp = requests.delete(f"{BASE_URL}/api/applications/{app_id}", headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


# --- Referrals ---
def create_referral(data: dict) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/referrals/", json=data, headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


def list_referrals() -> Optional[list]:
    resp = requests.get(f"{BASE_URL}/api/referrals/", headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


def update_referral(ref_id: int, data: dict) -> Optional[dict]:
    resp = requests.put(f"{BASE_URL}/api/referrals/{ref_id}", json=data, headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


def delete_referral(ref_id: int) -> Optional[dict]:
    resp = requests.delete(f"{BASE_URL}/api/referrals/{ref_id}", headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)


# --- Interview ---
def generate_interview(
    role: str,
    company: str = "",
    itype: str = "mixed",
    difficulty: str = "medium",
    num: int = 5,
) -> Optional[dict]:
    payload = {
        "role": role,
        "company": company,
        "interview_type": itype,
        "difficulty": difficulty,
        "num_questions": num,
    }
    resp = requests.post(f"{BASE_URL}/api/interview/generate", json=payload, headers=_headers(), timeout=_TIMEOUT_AI)
    return _handle_response(resp)


def evaluate_interview(question: str, answer: str, role: str) -> Optional[dict]:
    resp = requests.post(
        f"{BASE_URL}/api/interview/evaluate",
        json={"question": question, "answer": answer, "role": role},
        headers=_headers(),
        timeout=_TIMEOUT_AI,
    )
    return _handle_response(resp)


# --- Skills ---
def analyze_skill_gap(job_description: str, user_skills: list = None) -> Optional[dict]:
    resp = requests.post(
        f"{BASE_URL}/api/skills/analyze-gap",
        json={"job_description": job_description, "user_skills": user_skills},
        headers=_headers(),
        timeout=_TIMEOUT_AI,
    )
    return _handle_response(resp)


# --- Email ---
def generate_email(
    email_type: str,
    recipient: str = "",
    company: str = "",
    role: str = "",
    context: str = "",
    tone: str = "professional",
) -> Optional[dict]:
    payload = {
        "email_type": email_type,
        "recipient_name": recipient,
        "company": company,
        "role": role,
        "context": context,
        "tone": tone,
    }
    resp = requests.post(f"{BASE_URL}/api/email/generate", json=payload, headers=_headers(), timeout=_TIMEOUT_AI)
    return _handle_response(resp)


# --- GitHub ---
def analyze_github(username: str, max_repos: int = 10) -> Optional[dict]:
    resp = requests.post(
        f"{BASE_URL}/api/github/analyze",
        json={"username": username, "max_repos": max_repos},
        headers=_headers(),
        timeout=_TIMEOUT_AI,
    )
    return _handle_response(resp)


# --- Recruiter Simulator ---
def simulate_recruiter(resume_text: str, job_description: str) -> Optional[dict]:
    # FIX #3: Dedicated function for the correct recruiter endpoint
    resp = requests.post(
        f"{BASE_URL}/api/analyzer/simulate",
        json={"resume_text": resume_text, "job_description": job_description},
        headers=_headers(),
        timeout=_TIMEOUT_AI,
    )
    return _handle_response(resp)


# --- Extraction ---
def extract_jd(text: str = None, url: str = None) -> Optional[dict]:
    resp = requests.post(
        f"{BASE_URL}/api/extract/jd",
        json={"text": text, "url": url},
        headers=_headers(),
        timeout=_TIMEOUT_SHORT,
    )
    return _handle_response(resp)


# --- Analytics ---
def get_analytics() -> Optional[dict]:
    resp = requests.get(f"{BASE_URL}/api/analytics/summary", headers=_headers(), timeout=_TIMEOUT_SHORT)
    return _handle_response(resp)
