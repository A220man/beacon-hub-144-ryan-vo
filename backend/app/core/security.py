"""Security utilities for authentication and authorization."""

import secrets
import base64
import hashlib
from datetime import datetime, timedelta, UTC
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models import User


settings = get_settings()


def _hash_secret(secret: str) -> str:
    """Hash a secret using PBKDF2-HMAC-SHA256 (passlib 1.7.4 incompatible with bcrypt 5.0+)."""
    salt = secrets.token_bytes(16)
    hash_value = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, 100_000)
    return base64.b64encode(salt + hash_value).decode("ascii")


def _verify_secret(secret: str, stored: str) -> bool:
    """Verify a secret against stored PBKDF2 hash."""
    try:
        decoded = base64.b64decode(stored)
        salt = decoded[:16]
        hash_value = decoded[16:]
        expected = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, 100_000)
        return secrets.compare_digest(hash_value, expected)
    except Exception:
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return _verify_secret(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return _hash_secret(password)


def create_access_token(
    subject: str,
    roles: Optional[list[str]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    if roles:
        to_encode["roles"] = roles
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.PyJWTError:
        return None


def generate_state() -> str:
    """Generate a secure random state parameter for OAuth."""
    return secrets.token_urlsafe(32)


def generate_code_verifier() -> str:
    """Generate a PKCE code verifier."""
    return secrets.token_urlsafe(64)[:128]


def generate_code_challenge(verifier: str) -> str:
    """Generate a PKCE code challenge from verifier (S256)."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT cookie."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(access_token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_current_user_id(
    user: User = Depends(get_current_user),
) -> int:
    """Get current user ID."""
    return user.id
