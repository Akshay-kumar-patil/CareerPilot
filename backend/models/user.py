"""
MongoDB user document helper.
Replaces the SQLAlchemy User model for all auth and profile operations.
All persistence goes to the 'authentication' collection in MongoDB.
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId


def user_doc_to_response(doc: dict) -> dict:
    """Convert a MongoDB user document to a serialisable dict."""
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    # Ensure lists are never None
    for field in ("skills", "education", "work_experience", "projects"):
        if doc.get(field) is None:
            doc[field] = []
    doc.setdefault("experience_years", 0)
    return doc


def build_new_user_doc(email: str, hashed_password: str, full_name: str,
                       provider: str = "local") -> dict:
    """Return a dict ready to be inserted into the 'authentication' collection."""
    now = datetime.utcnow()
    return {
        "email": email,
        "hashed_password": hashed_password,
        "full_name": full_name,
        "auth_provider": provider,          # "local" | "google"
        "phone": None,
        "linkedin_url": None,
        "github_username": None,
        "portfolio_url": None,
        "skills": [],
        "experience_years": 0,
        "current_role": None,
        "target_role": None,
        "education": [],
        "work_experience": [],
        "projects": [],
        "summary": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
