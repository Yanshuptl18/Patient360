"""Unit tests for secret management and production safety validation."""

import pytest

from backend.core.config import Settings
from backend.core.secrets import generate_secure_secret_key, validate_secret_strength


def test_generate_secure_secret_key() -> None:
    key = generate_secure_secret_key(32)
    assert len(key) == 64
    assert isinstance(key, str)


def test_validate_secret_strength() -> None:
    # Weak keys
    assert validate_secret_strength("short")["valid"] is False
    assert validate_secret_strength("patient360_development_insecure_secret_key")["valid"] is False

    # Strong key
    strong = generate_secure_secret_key(32)
    result = validate_secret_strength(strong)
    assert result["valid"] is True
    assert result["length"] == 64


def test_production_settings_rejects_insecure_key() -> None:
    # Reject default key in production
    with pytest.raises(ValueError, match="Default development SECRET_KEY is strictly prohibited"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="patient360_development_insecure_secret_key_change_in_production_32chars",
            LLM_PROVIDER="gemini",
            GEMINI_API_KEY="valid_mock_api_key_for_testing",
        )

    # Reject short key in production
    with pytest.raises(ValueError, match="must be at least 32 characters"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="too_short_key",
            LLM_PROVIDER="gemini",
            GEMINI_API_KEY="valid_mock_api_key_for_testing",
        )

    # Accept valid strong key
    valid_key = generate_secure_secret_key(32)
    s = Settings(
        ENVIRONMENT="production",
        SECRET_KEY=valid_key,
        LLM_PROVIDER="gemini",
        GEMINI_API_KEY="valid_mock_api_key_for_testing",
    )
    assert s.SECRET_KEY == valid_key
