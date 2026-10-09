"""Cryptographic security utilities: password hashing and JWT token management."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from backend.core.config import settings
from backend.core.exceptions import AuthenticationError

# Configure password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored bcrypt hash."""
    return bool(pwd_context.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    """Generates a secure bcrypt hash for a plaintext password."""
    return str(pwd_context.hash(password))


def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Creates a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Creates a signed JWT refresh token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "refresh",
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    """
    Decodes and validates a JWT token.
    Raises AuthenticationError if expired, malformed, or of invalid type.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if expected_type and payload.get("type") != expected_type:
            raise AuthenticationError(f"Invalid token type: expected {expected_type}")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired. Please re-authenticate.") from None
    except (jwt.InvalidTokenError, Exception) as exc:
        raise AuthenticationError(f"Invalid authentication token: {str(exc)}") from exc
