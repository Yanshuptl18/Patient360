"""Unit tests for cryptographic password hashing and JWT management."""

from datetime import timedelta

import pytest

from backend.core.exceptions import AuthenticationError
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    """Verifies that bcrypt correctly hashes and verifies passwords."""
    raw_password = "ClinicalSecretPassword123!"
    hashed = get_password_hash(raw_password)

    assert hashed != raw_password
    assert hashed.startswith("$2b$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_create_and_decode_access_token() -> None:
    """Verifies that access tokens are correctly created, signed, and decoded."""
    user_id = "test-uuid-1234-5678"
    role = "reviewer"
    token = create_access_token(subject=user_id, role=role)

    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_and_decode_refresh_token() -> None:
    """Verifies that refresh tokens are correctly created and verified."""
    user_id = "test-uuid-refresh"
    role = "researcher"
    token = create_refresh_token(subject=user_id, role=role)

    payload = decode_token(token, expected_type="refresh")
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "refresh"


def test_token_type_mismatch_raises_error() -> None:
    """Verifies that decoding an access token when expecting refresh raises an error."""
    token = create_access_token(subject="user-123", role="demo")
    with pytest.raises(AuthenticationError, match="Invalid token type"):
        decode_token(token, expected_type="refresh")


def test_expired_token_raises_error() -> None:
    """Verifies that an expired JWT raises an AuthenticationError."""
    expired_token = create_access_token(
        subject="user-expired",
        role="reviewer",
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )
    with pytest.raises(AuthenticationError, match="Token has expired"):
        decode_token(expired_token)


def test_tampered_token_raises_error() -> None:
    """Verifies that a tampered token signature raises AuthenticationError."""
    token = create_access_token(subject="user-123", role="admin")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(AuthenticationError, match="Invalid authentication token"):
        decode_token(tampered)
