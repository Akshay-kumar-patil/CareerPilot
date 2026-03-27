"""
API client for Streamlit frontend to communicate with FastAPI backend.
"""
import os
import requests
import streamlit as st
from typing import Optional, Dict, Any

BASE_URL = os.environ.get("API_BASE_URL", "https://career-portal-m5re.onrender.com")


def _headers() -> dict:
    """Get auth headers from session state."""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _handle_response(resp: requests.Response) -> dict:
    """Handle API response, showing errors in Streamlit."""
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 401:
        st.session_state.pop("token", None)
        st.session_state.pop("user", None)
        st.error("Session expired. Please log in again.")
        return None
    else:
        detail = resp.json().get("detail", "Unknown error") if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        st.error(f"API Error: {detail}")
        return None


# --- Auth ---
def register(email: str, password: str, full_name: str) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": password, "full_name": full_name})
    return _handle_response(resp)


def login(email: str, password: str) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    return _handle_response(resp)


def get_me() -> Optional[dict]:
    resp = requests.get(f"{BASE_URL}/api/auth/me", headers=_headers())
    return _handle_response(resp)


def update_profile(data: dict) -> Optional[dict]:
    resp = requests.put(f"{BASE_URL}/api/auth/profile", json=data, headers=_headers())
    return _handle_response(resp)


# --- AI Status ---
def get_ai_status() -> Optional[dict]:
    try:
        resp = requests.get(f"{BASE_URL}/api/ai/status", timeout=3)
        return resp.json()
    except Exception:
        return None


# --- Resume ---
def generate_resume(job_description: str, existing_resume: str = "", template_id: int = None, additional_context: str = "") -> Optional[dict]:
    payload = {"job_description": job_description, "existing_resume": existing_resume, "additional_context": additional_context}
    if template_id:
        payload["template_id"] = template_id
    resp = requests.post(f"{BASE_URL}/api/resume/generate", json=payload, headers=_headers(), timeout=120)
    return _handle_response(resp)


def list_resumes() -> Optional[list]:
    resp = requests.get(f"{BASE_URL}/api/resume/list", headers=_headers())
    return _handle_response(resp)


def get_resume(resume_id: int) -> Optional[dict]:
    resp = requests.get(f"{BASE_URL}/api/resume/{resume_id}", headers=_headers())
    return _handle_response(resp)


def download_resume(resume_id: int, fmt: str) -> Optional[bytes]:
    resp = requests.post(f"{BASE_URL}/api/resume/{resume_id}/download/{fmt}", headers=_headers(), timeout=30)
    if resp.status_code == 200:
        return resp.content
    return None


# --- Analyzer ---
def analyze_resume(resume_text: str, job_description: str = "") -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/analyzer/analyze", json={"resume_text": resume_text, "job_description": job_description}, headers=_headers(), timeout=120)
    return _handle_response(resp)


def quick_score(resume_text: str, job_description: str) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/analyzer/quick-score", json={"resume_text": resume_text, "job_description": job_description}, headers=_headers())
    return _handle_response(resp)


# --- Cover Letter ---
def generate_cover_letter(company: str, role: str, jd: str = "", skills: list = None, tone: str = "formal", context: str = "") -> Optional[dict]:
    payload = {"company_name": company, "role": role, "job_description": jd, "key_skills": skills or [], "tone": tone, "additional_context": context}
    resp = requests.post(f"{BASE_URL}/api/cover-letter/generate", json=payload, headers=_headers(), timeout=120)
    return _handle_response(resp)


# --- Applications ---
def create_application(data: dict) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/applications/", json=data, headers=_headers())
    return _handle_response(resp)


def list_applications(status: str = None) -> Optional[list]:
    params = {"status": status} if status else {}
    resp = requests.get(f"{BASE_URL}/api/applications/", params=params, headers=_headers())
    return _handle_response(resp)


def update_application(app_id: int, data: dict) -> Optional[dict]:
    resp = requests.put(f"{BASE_URL}/api/applications/{app_id}", json=data, headers=_headers())
    return _handle_response(resp)


def delete_application(app_id: int) -> Optional[dict]:
    resp = requests.delete(f"{BASE_URL}/api/applications/{app_id}", headers=_headers())
    return _handle_response(resp)


# --- Referrals ---
def create_referral(data: dict) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/referrals/", json=data, headers=_headers())
    return _handle_response(resp)


def list_referrals() -> Optional[list]:
    resp = requests.get(f"{BASE_URL}/api/referrals/", headers=_headers())
    return _handle_response(resp)


def update_referral(ref_id: int, data: dict) -> Optional[dict]:
    resp = requests.put(f"{BASE_URL}/api/referrals/{ref_id}", json=data, headers=_headers())
    return _handle_response(resp)


def delete_referral(ref_id: int) -> Optional[dict]:
    resp = requests.delete(f"{BASE_URL}/api/referrals/{ref_id}", headers=_headers())
    return _handle_response(resp)


# --- Interview ---
def generate_interview(role: str, company: str = "", itype: str = "mixed", difficulty: str = "medium", num: int = 5) -> Optional[dict]:
    payload = {"role": role, "company": company, "interview_type": itype, "difficulty": difficulty, "num_questions": num}
    resp = requests.post(f"{BASE_URL}/api/interview/generate", json=payload, headers=_headers(), timeout=120)
    return _handle_response(resp)


def evaluate_interview(question: str, answer: str, role: str) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/interview/evaluate", json={"question": question, "answer": answer, "role": role}, headers=_headers(), timeout=120)
    return _handle_response(resp)


# --- Skills ---
def analyze_skill_gap(job_description: str, user_skills: list = None) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/skills/analyze-gap", json={"job_description": job_description, "user_skills": user_skills}, headers=_headers(), timeout=120)
    return _handle_response(resp)


# --- Email ---
def generate_email(email_type: str, recipient: str = "", company: str = "", role: str = "", context: str = "", tone: str = "professional") -> Optional[dict]:
    payload = {"email_type": email_type, "recipient_name": recipient, "company": company, "role": role, "context": context, "tone": tone}
    resp = requests.post(f"{BASE_URL}/api/email/generate", json=payload, headers=_headers(), timeout=120)
    return _handle_response(resp)


# --- GitHub ---
def analyze_github(username: str, max_repos: int = 10) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/github/analyze", json={"username": username, "max_repos": max_repos}, headers=_headers(), timeout=120)
    return _handle_response(resp)


# --- Extraction ---
def extract_jd(text: str = None, url: str = None) -> Optional[dict]:
    resp = requests.post(f"{BASE_URL}/api/extract/jd", json={"text": text, "url": url}, headers=_headers(), timeout=60)
    return _handle_response(resp)


# --- Analytics ---
def get_analytics() -> Optional[dict]:
    resp = requests.get(f"{BASE_URL}/api/analytics/summary", headers=_headers())
    return _handle_response(resp)
