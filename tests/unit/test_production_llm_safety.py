"""Unit tests for production LLM safety and zero-mock enforcement."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from backend.core.config import settings
from backend.core.exceptions import ConfigurationError, LLMProviderUnavailableError
from backend.rag.llm import (
    GeminiLLMProvider,
    MockLLMProvider,
    get_llm_provider,
    reset_llm_provider,
)


def test_production_environment_rejects_missing_gemini_key() -> None:
    """Verifies that in production mode, missing Gemini key raises ConfigurationError rather than silent mock fallback."""
    reset_llm_provider()
    try:
        with patch.object(settings, "ENVIRONMENT", "production"), \
             patch.object(settings, "LLM_PROVIDER", "gemini"), \
             patch.object(settings, "GEMINI_API_KEY", ""), \
             patch.object(settings, "ALLOW_MOCK_IN_PRODUCTION", False):
            with pytest.raises(ConfigurationError, match="GEMINI_API_KEY is not configured in production"):
                get_llm_provider()
    finally:
        reset_llm_provider()


def test_production_environment_rejects_explicit_mock_provider() -> None:
    """Verifies that in production mode, setting LLM_PROVIDER=mock raises ConfigurationError."""
    reset_llm_provider()
    try:
        with patch.object(settings, "ENVIRONMENT", "production"), \
             patch.object(settings, "LLM_PROVIDER", "mock"), \
             patch.object(settings, "ALLOW_MOCK_IN_PRODUCTION", False):
            with pytest.raises(ConfigurationError, match="MockLLMProvider is strictly prohibited"):
                get_llm_provider()
    finally:
        reset_llm_provider()


def test_development_fallback_to_mock_allowed() -> None:
    """Verifies that in non-production mode, fallback to mock remains functional for offline dev and CI."""
    reset_llm_provider()
    try:
        with patch.object(settings, "ENVIRONMENT", "development"), \
             patch.object(settings, "LLM_PROVIDER", "gemini"), \
             patch.object(settings, "GEMINI_API_KEY", ""), \
             patch.object(settings, "LLM_FALLBACK_TO_MOCK", True):
            provider = get_llm_provider()
            assert isinstance(provider, MockLLMProvider)
            assert provider.provider_name == "mock"
    finally:
        reset_llm_provider()


def test_gemini_unconfigured_key_raises_llm_unavailable() -> None:
    """Verifies that calling generate_answer with empty key raises LLMProviderUnavailableError."""
    provider = GeminiLLMProvider(api_key="")
    with pytest.raises(LLMProviderUnavailableError) as exc_info:
        provider.generate_answer("Prompt", "System")
    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "LLM_PROVIDER_UNAVAILABLE"


def test_gemini_quota_exhaustion_raises_llm_unavailable() -> None:
    """Verifies that HTTP 429 quota exhaustion raises LLMProviderUnavailableError after retries."""
    response_429 = MagicMock(spec=httpx.Response)
    response_429.status_code = 429
    response_429.text = "Resource exhausted: quota exceeded"

    with patch("httpx.Client.post", return_value=response_429), patch("time.sleep"):
        provider = GeminiLLMProvider(api_key="AQ.VALID_KEY")
        with pytest.raises(LLMProviderUnavailableError) as exc_info:
            provider.generate_answer("Prompt", "System")
        assert exc_info.value.status_code == 503
        assert "429" in exc_info.value.message or "rate limit" in exc_info.value.message.lower()
        assert exc_info.value.details.get("status_code") == 429


def test_gemini_invalid_key_raises_llm_unavailable() -> None:
    """Verifies that HTTP 400/403 invalid API key raises LLMProviderUnavailableError."""
    response_403 = MagicMock(spec=httpx.Response)
    response_403.status_code = 403
    response_403.text = "Forbidden"
    response_403.json.return_value = {"error": {"message": "API key not valid. Please pass a valid API key."}}

    with patch("httpx.Client.post", return_value=response_403):
        provider = GeminiLLMProvider(api_key="AQ.INVALID_KEY")
        with pytest.raises(LLMProviderUnavailableError) as exc_info:
            provider.generate_answer("Prompt", "System")
        assert exc_info.value.status_code == 503
        assert "authentication failed" in exc_info.value.message.lower()
        assert exc_info.value.details.get("status_code") == 403


def test_gemini_timeout_raises_llm_unavailable() -> None:
    """Verifies that timeout raises LLMProviderUnavailableError with 503 status code."""
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Timed out")), patch("time.sleep"):
        provider = GeminiLLMProvider(api_key="AQ.VALID_KEY", timeout_seconds=5.0)
        with pytest.raises(LLMProviderUnavailableError) as exc_info:
            provider.generate_answer("Prompt", "System")
        assert exc_info.value.status_code == 503
        assert "timed out" in exc_info.value.message.lower()


def test_gemini_network_error_raises_llm_unavailable() -> None:
    """Verifies that connection failures raise LLMProviderUnavailableError with 503 status code."""
    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Network unreachable")), patch("time.sleep"):
        provider = GeminiLLMProvider(api_key="AQ.VALID_KEY")
        with pytest.raises(LLMProviderUnavailableError) as exc_info:
            provider.generate_answer("Prompt", "System")
        assert exc_info.value.status_code == 503
        assert "connection failed" in exc_info.value.message.lower() or "failed" in exc_info.value.message.lower()


def test_gemini_successful_response_metadata() -> None:
    """Verifies that successful response includes provider='gemini'."""
    mock_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Patient has stable vital signs [Doc: 1, Page 1]."}]
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 25,
            "candidatesTokenCount": 10,
        },
    }
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_payload

    with patch("httpx.Client.post", return_value=mock_response):
        provider = GeminiLLMProvider(api_key="AQ.VALID_KEY")
        resp = provider.generate_answer("Vital signs?", "System")
        assert resp.provider == "gemini"
        assert resp.content == "Patient has stable vital signs [Doc: 1, Page 1]."

