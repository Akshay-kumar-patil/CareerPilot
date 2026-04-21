"""JWT authentication utilities — uses MongoDB as the user store."""
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.config import settings
from backend.database import get_users_collection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer — accepts "Authorization: Bearer <token>" headers
http_bearer = HTTPBearer(auto_error=True)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> dict:
    """
    Validate JWT and return the MongoDB user document as a plain dict.
    The 'id' key is the string representation of the ObjectId.
    """
    payload = decode_token(credentials.credentials)
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        oid = ObjectId(user_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=401, detail="Invalid user ID in token")

    col = get_users_collection()
    if col is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_doc = col.find_one({"_id": oid})
    if user_doc is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Normalise: expose 'id' as string, keep '_id' too for internal use
    user_doc["id"] = str(user_doc["_id"])
    return user_doc
