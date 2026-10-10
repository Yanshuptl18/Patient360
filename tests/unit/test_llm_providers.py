"""Comprehensive unit tests for Multi-Provider LLM Gateway: Mock, Gemini, and Ollama."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from backend.core.config import settings
from backend.rag.llm import (
    GeminiLLMProvider,
    MockLLMProvider,
    OllamaLLMProvider,
    get_llm_provider,
    reset_llm_provider,
)


def test_mock_llm_provider_generation_and_health() -> None:
    """Verifies MockLLMProvider operates offline with zero cost."""
    provider = MockLLMProvider()
    resp = provider.generate_answer("Prompt", "System")
    assert resp.content
    assert resp.model == "mock-clinical-grounded-v1"
    assert resp.latency_ms >= 1

    ok, lat, msg = provider.check_health()
    assert ok is True
    assert "Zero API cost" in msg

    summary = provider.summarize_document("Clinical summary text", max_tokens=50)
    assert "clinical" in summary.lower()

    extracted = provider.extract_structured("Patient has diabetes", target_schema="{'condition': str}")
    assert "findings" in extracted


def test_gemini_provider_unconfigured_key() -> None:
    """Verifies GeminiLLMProvider raises error or fails health if key is empty."""
    provider = GeminiLLMProvider(api_key="")
    with pytest.raises((ValueError, RuntimeError), match="GEMINI_API_KEY is not configured"):
        provider.generate_answer("Hello", "System")

    ok, lat, msg = provider.check_health()
    assert ok is False
    assert "not configured" in msg


def test_gemini_provider_successful_generation() -> None:
    """Verifies GeminiLLMProvider parses candidates and token usage from Google API."""
    mock_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "EGFR mutation detected in exon 21 [Doc: 1, Page 2]."}]
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 42,
            "candidatesTokenCount": 15,
        },
    }

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_payload

    with patch("httpx.Client.post", return_value=mock_response):
        provider = GeminiLLMProvider(api_key="AQ.TEST_MOCK_KEY", model_name="gemini-3.5-flash-lite")
        resp = provider.generate_answer("What mutation?", "System")

        assert "EGFR mutation detected" in resp.content
        assert resp.prompt_tokens == 42
        assert resp.completion_tokens == 15
        assert resp.model == "gemini-3.5-flash-lite"


def test_gemini_provider_rate_limit_retry() -> None:
    """Verifies GeminiLLMProvider handles HTTP 429 with backoff retry."""
    response_429 = MagicMock(spec=httpx.Response)
    response_429.status_code = 429

    response_200 = MagicMock(spec=httpx.Response)
    response_200.status_code = 200
    response_200.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Recovered after retry"}]}}],
        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5},
    }

    with patch("httpx.Client.post", side_effect=[response_429, response_200]), patch("time.sleep") as mock_sleep:
        provider = GeminiLLMProvider(api_key="AQ.TEST_MOCK_KEY")
        resp = provider.generate_answer("Prompt", "System")

        assert resp.content == "Recovered after retry"
        assert mock_sleep.called


def test_gemini_provider_health_check() -> None:
    """Verifies GeminiLLMProvider health check responds to Google API status."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    with patch("httpx.Client.get", return_value=mock_response):
        provider = GeminiLLMProvider(api_key="AQ.TEST_MOCK_KEY")
        ok, lat, msg = provider.check_health()
        assert ok is True
        assert "online" in msg


def test_ollama_provider_successful_generation() -> None:
    """Verifies OllamaLLMProvider parses local Ollama REST responses."""
    mock_payload = {
        "response": "Synthesized clinical findings from Qwen3 4B.",
        "prompt_eval_count": 28,
        "eval_count": 12,
    }
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_payload

    with patch("httpx.Client.post", return_value=mock_response):
        provider = OllamaLLMProvider(base_url="http://localhost:11434", model_name="qwen3:4b")
        resp = provider.generate_answer("Prompt", "System")

        assert "Qwen3 4B" in resp.content
        assert resp.prompt_tokens == 28
        assert resp.completion_tokens == 12


def test_ollama_provider_missing_model_guidance() -> None:
    """Verifies actionable error guidance if Qwen3 4B model is missing."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404

    with patch("httpx.Client.post", return_value=mock_response):
        provider = OllamaLLMProvider(model_name="qwen3:4b")
        with pytest.raises(RuntimeError, match="ollama pull qwen3:4b"):
            provider.generate_answer("Prompt", "System")


def test_ollama_provider_unreachable_connection_error() -> None:
    """Verifies clean error when local Ollama daemon is offline."""
    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection refused")):
        provider = OllamaLLMProvider()
        with pytest.raises(RuntimeError, match="Ensure Ollama is installed and running"):
            provider.generate_answer("Prompt", "System")


def test_ollama_provider_health_check() -> None:
    """Verifies Ollama health check detects tags list."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": [{"name": "qwen3:4b-q4_k_m"}]}

    with patch("httpx.Client.get", return_value=mock_response):
        provider = OllamaLLMProvider(model_name="qwen3:4b")
        ok, lat, msg = provider.check_health()
        assert ok is True
        assert "qwen3:4b" in msg


def test_get_llm_provider_fallback() -> None:
    """Verifies get_llm_provider falls back to MockLLMProvider when keys are absent."""
    reset_llm_provider()
    with patch.object(settings, "LLM_PROVIDER", "gemini"), patch.object(
        settings, "GEMINI_API_KEY", ""
    ), patch.object(settings, "LLM_FALLBACK_TO_MOCK", True):
        provider = get_llm_provider()
        assert isinstance(provider, MockLLMProvider)
    reset_llm_provider()
