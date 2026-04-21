"""
Authentication API routes — MongoDB-primary.

Supports:
  - POST /api/auth/register   → create user in MongoDB
  - POST /api/auth/login      → verify credentials from MongoDB
  - GET  /api/auth/me         → return current user profile
  - PUT  /api/auth/profile    → update user profile in MongoDB
  - GET  /api/auth/google     → redirect to Google OAuth
  - GET  /api/auth/google/callback → handle Google OAuth callback
  - GET  /api/auth/google/status   → check if Google OAuth is configured
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError

from backend.config import settings
from backend.database import get_users_collection
from backend.models.user import build_new_user_doc, user_doc_to_response
from backend.schemas.user import (
    UserRegister, UserLogin, UserProfile, UserResponse, TokenResponse,
)
from backend.utils.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ─── Google OAuth client (authlib) ─────────────────────────────────────────────
_oauth = None


def _get_oauth():
    """Lazily create the OAuth client so missing credentials don't crash startup."""
    global _oauth
    if _oauth is not None:
        return _oauth
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return None
    try:
        from authlib.integrations.starlette_client import OAuth
        oauth = OAuth()
        oauth.register(
            name="google",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
        _oauth = oauth
        return _oauth
    except Exception as exc:
        logger.warning("Google OAuth not available: %s", exc)
        return None


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _user_response(doc: dict) -> UserResponse:
    """Convert a MongoDB doc to UserResponse."""
    d = user_doc_to_response(doc)
    return UserResponse(**d)


# ─── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister):
    col = get_users_collection()
    if col is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Check duplicate
    if col.find_one({"email": data.email.strip().lower()}):
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = build_new_user_doc(
        email=data.email.strip().lower(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name.strip(),
        provider="local",
    )

    try:
        result = col.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")

    doc["_id"] = result.inserted_id
    token = create_access_token({"sub": str(result.inserted_id)})

    logger.info("New user registered: %s", data.email)
    return TokenResponse(
        access_token=token,
        user=_user_response(doc),
    )


# ─── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin):
    col = get_users_collection()
    if col is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_doc = col.find_one({"email": data.email.strip().lower()})
    if not user_doc or not verify_password(data.password, user_doc.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user_doc["_id"])})

    logger.info("User logged in: %s", data.email)
    return TokenResponse(
        access_token=token,
        user=_user_response(user_doc),
    )


# ─── Get current user ──────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return _user_response(current_user)


# ─── Update profile ────────────────────────────────────────────────────────────

@router.put("/profile")
def update_profile(
    data: UserProfile,
    current_user: dict = Depends(get_current_user),
):
    col = get_users_collection()
    if col is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    updates = data.model_dump(exclude_none=True)
    if not updates:
        return {"message": "No changes provided"}

    updates["updated_at"] = datetime.utcnow()

    from bson import ObjectId
    col.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": updates},
    )

    logger.info("Profile updated for user: %s", current_user["email"])
    return {"message": "Profile updated", "user_id": current_user["id"]}


# ─── Google OAuth ──────────────────────────────────────────────────────────────

@router.get("/google")
async def google_login(request: Request):
    """Redirect the browser to Google's consent screen."""
    oauth = _get_oauth()
    if oauth is None:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@router.get("/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback, issue a JWT, redirect to frontend."""
    oauth = _get_oauth()
    if oauth is None:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured.")

    try:
        token_data = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        logger.error("Google OAuth token exchange failed: %s", exc)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?oauth_error=token_exchange_failed",
            status_code=302,
        )

    user_info = token_data.get("userinfo") or {}
    email = user_info.get("email", "").strip().lower()
    full_name = user_info.get("name", email)

    if not email:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?oauth_error=no_email",
            status_code=302,
        )

    col = get_users_collection()
    user_doc = col.find_one({"email": email})

    if not user_doc:
        # Create new user
        doc = build_new_user_doc(email=email, hashed_password="", full_name=full_name, provider="google")
        result = col.insert_one(doc)
        doc["_id"] = result.inserted_id
        user_doc = doc
        logger.info("New user created via Google OAuth: %s", email)
    else:
        # Update name if changed
        if full_name and user_doc.get("full_name") != full_name:
            col.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"full_name": full_name, "updated_at": datetime.utcnow()}},
            )
            user_doc["full_name"] = full_name

    jwt_token = create_access_token({"sub": str(user_doc["_id"])})
    redirect_url = f"{settings.FRONTEND_URL}/?auth_token={jwt_token}"
    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/google/status")
def google_oauth_status():
    """Check whether Google OAuth is configured on this server."""
    configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    return {
        "configured": configured,
        "login_url": "/api/auth/google" if configured else None,
        "hint": (
            "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env to enable Google login."
            if not configured else None
        ),
    }
