"""Security utilities for authentication and authorization."""

import secrets
import hashlib
import hmac
import base64
from datetime import datetime, timedelta, UTC
from typing import Optional
from jose import jwt, JWTError

from app.core.config import get_settings


settings = get_settings()


def _hash_secret(secret: str) -> str:
    """Hash a secret using PBKDF2-HMAC-SHA256 (passlib 1.7.4 incompatible with bcrypt 5.0+)."""
    salt = secrets.token_bytes(32)
    hash_value = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, iterations=600000, dklen=32)
    return base64.b64encode(salt + hash_value).decode("ascii")


def _verify_secret(secret: str, stored: str) -> bool:
    """Verify a secret against stored PBKDF2 hash."""
    try:
        raw = base64.b64decode(stored.encode("ascii"))
        salt = raw[:32]
        stored_hash = raw[32:]
        test_hash = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, iterations=600000, dklen=32)
        return hmac.compare_digest(stored_hash, test_hash)
    except (ValueError, Exception):
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return _verify_secret(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return _hash_secret(password)


def create_access_token(
    subject: str,
    roles: list[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {
        "sub": subject,
        "roles": roles,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def generate_state() -> str:
    """Generate a secure random state parameter for OAuth."""
    return secrets.token_urlsafe(32)


def generate_code_verifier() -> str:
    """Generate a PKCE code verifier."""
    return secrets.token_urlsafe(64)[:128]


def generate_code_challenge(verifier: str) -> str:
    """Generate a PKCE code challenge from verifier (S256)."""
    import hashlib
    import base64
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")