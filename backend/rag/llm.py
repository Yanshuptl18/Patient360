"""Multi-provider LLM gateway supporting Gemini, Ollama (Qwen3 4B), and deterministic Mock."""

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from backend.core.config import settings
from backend.core.exceptions import ConfigurationError, LLMProviderUnavailableError

logger = logging.getLogger(__name__)

ABSTENTION_MESSAGE = "Insufficient evidence documented in available records."


@dataclass
class LLMResponse:
    """Standardized response from an LLM provider."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    provider: str = "mock"


class BaseLLMProvider(ABC):
    """Abstract base contract for multi-provider LLM generation."""

    provider_name: str = "base"

    @abstractmethod
    def generate_answer(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Generates an evidence-grounded answer given the structured prompt."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        schema_description: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Generates structured JSON adhering to the specified schema description."""
        pass

    @abstractmethod
    def summarize_document(
        self,
        text: str,
        max_tokens: int = 300,
    ) -> str:
        """Summarizes medical document text concisely."""
        pass

    @abstractmethod
    def extract_structured(
        self,
        text: str,
        target_schema: str,
    ) -> dict[str, Any]:
        """Extracts structured clinical parameters from text according to target schema."""
        pass

    @abstractmethod
    def check_health(self) -> tuple[bool, int, str]:
        """
        Probes provider availability and connectivity.
        Returns: (is_healthy, latency_ms, status_message)
        """
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic clinical LLM provider for tests, CI, and offline zero-cost development.
    Synthesizes findings directly from context passages with [Doc: {id}, Page: {no}] tags.
    """

    provider_name: str = "mock"

    def __init__(self, model_name: str = "mock-clinical-grounded-v1") -> None:
        self.model_name = model_name

    def generate_answer(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> LLMResponse:
        start_time = time.perf_counter()

        # Extract passages: <<<UNTRUSTED_DOCUMENT_CONTENT [Doc: {doc_id}, Page: {page_no}]>>>\n{content}\n<<<END_UNTRUSTED_DOCUMENT_CONTENT>>>
        passage_pattern = re.compile(
            r"<<<UNTRUSTED_DOCUMENT_CONTENT\s+\[Doc:\s*([a-zA-Z0-9_\-]+),\s*Page:\s*(\d+)\]>>>\s*(.*?)\s*<<<END_UNTRUSTED_DOCUMENT_CONTENT>>>",
            re.DOTALL,
        )
        passages: list[tuple[str, int, str]] = []
        for match in passage_pattern.finditer(prompt):
            doc_id = match.group(1).strip()
            page_no = int(match.group(2).strip())
            content = match.group(3).strip()
            passages.append((doc_id, page_no, content))

        # Extract user inquiry from prompt: "Clinical Inquiry: {query}"
        inquiry_match = re.search(r"Clinical Inquiry:\s*(.+)$", prompt, re.DOTALL)
        query = inquiry_match.group(1).strip().lower() if inquiry_match else ""

        # Check if query matches facts in retrieved passages
        has_relevant_evidence = False

        query_tokens = set(re.findall(r"[a-z0-9\-]+", query))
        stopwords = {
            "what", "is", "the", "a", "an", "this", "that", "in", "on", "of", "and", "or",
            "patient", "has", "have", "had", "for", "with", "any", "are", "were", "to",
            "does", "do", "did", "reported", "documented", "there", "show", "showed",
        }
        clinical_keywords = query_tokens - stopwords

        scored_statements: list[tuple[int, str]] = []

        for doc_id, page_no, content in passages:
            cleaned_content = re.sub(r"^\[Document:.*?\]\s*", "", content, flags=re.IGNORECASE).strip()
            content_lower = cleaned_content.lower()

            matched_kw = [kw for kw in clinical_keywords if kw in content_lower]

            if matched_kw:
                has_relevant_evidence = True
                sentences = [
                    s.strip()
                    for s in re.split(r"\n|(?<=[.!?])\s+", cleaned_content)
                    if s.strip()
                ]
                for sent in sentences:
                    sent_lower = sent.lower()
                    overlap_kws = [kw for kw in clinical_keywords if kw in sent_lower]
                    if overlap_kws:
                        citation_tag = f"[Doc: {doc_id}, Page: {page_no}]"
                        clean_sent = re.sub(r"^\[.*?\]\s*", "", sent).strip().rstrip(".")
                        if clean_sent and len(clean_sent) > 10:
                            score = len(overlap_kws)
                            statement = f"{clean_sent} {citation_tag}."
                            scored_statements.append((score, statement))

        if not has_relevant_evidence or not scored_statements:
            content_output = ABSTENTION_MESSAGE
        else:
            scored_statements.sort(key=lambda x: x[0], reverse=True)
            seen = set()
            unique_statements: list[str] = []
            for _, stmt in scored_statements:
                if stmt not in seen:
                    seen.add(stmt)
                    unique_statements.append(stmt)

            content_output = " ".join(unique_statements[:4])

        latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        prompt_tokens = len(prompt.split())
        completion_tokens = len(content_output.split())

        return LLMResponse(
            content=content_output,
            model=self.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            provider="mock",
        )

    def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        schema_description: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        resp = self.generate_answer(prompt, system_prompt, temperature)
        return {
            "summary": resp.content,
            "provenance": "mock_deterministic",
            "schema": schema_description,
            "status": "extracted",
        }

    def summarize_document(self, text: str, max_tokens: int = 300) -> str:
        lines = [line.strip() for line in text.split("\n") if line.strip() and not line.startswith("[")]
        summary = " ".join(lines[:3]) if lines else "Document summary unavailable."
        words = summary.split()
        if len(words) > max_tokens:
            summary = " ".join(words[:max_tokens]) + "..."
        return summary

    def extract_structured(self, text: str, target_schema: str) -> dict[str, Any]:
        return {
            "source_length": len(text),
            "target_schema": target_schema,
            "findings": [line[:80] for line in text.split("\n")[:3] if line.strip()],
        }

    def check_health(self) -> tuple[bool, int, str]:
        return True, 1, f"Mock LLM provider online ({self.model_name}) (Zero API cost)"


class GeminiLLMProvider(BaseLLMProvider):
    """
    Hosted Google Gemini integration via Generative Language REST API.
    Free tier eligible (e.g. gemini-3.5-flash-lite).
    """

    provider_name: str = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.timeout_seconds = timeout_seconds
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def generate_answer(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> LLMResponse:
        if not self.api_key:
            raise LLMProviderUnavailableError(
                "GEMINI_API_KEY is not configured in environment.",
                details={"provider": "gemini", "reason": "unconfigured_key"},
            )

        start_time = time.perf_counter()
        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        # Execute with bounded retries for rate-limiting (HTTP 429)
        max_retries = 2
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    res = client.post(url, json=payload)

                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise LLMProviderUnavailableError(
                            "Gemini returned zero candidates.",
                            details={"provider": "gemini", "reason": "empty_candidates"},
                        )

                    parts = candidates[0].get("content", {}).get("parts", [])
                    content_text = "".join(p.get("text", "") for p in parts)

                    usage = data.get("usageMetadata", {})
                    prompt_tokens = usage.get("promptTokenCount", len(prompt.split()))
                    completion_tokens = usage.get("candidatesTokenCount", len(content_text.split()))
                    latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))

                    return LLMResponse(
                        content=content_text,
                        model=self.model_name,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        latency_ms=latency_ms,
                        provider="gemini",
                    )

                if res.status_code == 429:
                    if attempt < max_retries:
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    raise LLMProviderUnavailableError(
                        "Gemini API rate limit or quota exceeded (HTTP 429). Please retry shortly.",
                        details={"provider": "gemini", "status_code": 429},
                    )

                if res.status_code in (400, 401, 403):
                    err_msg = res.json().get("error", {}).get("message", res.text)
                    raise LLMProviderUnavailableError(
                        f"Gemini API authentication failed (HTTP {res.status_code}): {err_msg}",
                        details={"provider": "gemini", "status_code": res.status_code},
                    )

                if res.status_code == 404:
                    err_msg = res.json().get("error", {}).get("message", res.text)
                    raise LLMProviderUnavailableError(
                        f"Gemini model '{self.model_name}' unavailable (HTTP 404): {err_msg}",
                        details={"provider": "gemini", "status_code": 404},
                    )

                res.raise_for_status()

            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < max_retries:
                    time.sleep(1.0)
                    continue
                raise LLMProviderUnavailableError(
                    f"Gemini request timed out after {self.timeout_seconds}s.",
                    details={"provider": "gemini", "reason": "timeout"},
                ) from exc
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt < max_retries:
                    time.sleep(1.0)
                    continue
                raise LLMProviderUnavailableError(
                    f"Gemini connection failed: {exc}",
                    details={"provider": "gemini", "reason": "network_error"},
                ) from exc
            except LLMProviderUnavailableError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= max_retries:
                    break

        raise LLMProviderUnavailableError(
            f"Gemini generation failed: {last_error}",
            details={"provider": "gemini", "reason": "generation_failure"},
        )

    def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        schema_description: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        augmented_prompt = (
            f"{prompt}\n\n"
            f"CRITICAL: Output strictly valid JSON conforming to the following schema:\n"
            f"{schema_description}\nDo not wrap output in markdown fences."
        )
        resp = self.generate_answer(augmented_prompt, system_prompt, temperature)
        raw_text = resp.content.strip()
        # Clean potential markdown fences
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)
        try:
            return dict(json.loads(raw_text))
        except Exception:
            return {"raw_output": resp.content, "parsed": False}

    def summarize_document(self, text: str, max_tokens: int = 300) -> str:
        prompt = f"Please provide a concise medical summary of the following document in under {max_tokens} words:\n\n{text}"
        system = "You are a clinical summarization assistant. Extract only factual documented patient information."
        resp = self.generate_answer(prompt, system, temperature=0.0)
        return resp.content

    def extract_structured(self, text: str, target_schema: str) -> dict[str, Any]:
        prompt = f"Extract structured clinical data from the following document:\n\n{text}"
        system = "You are a clinical data extraction assistant. Return structured JSON only."
        return self.generate_structured(prompt, system, target_schema, temperature=0.0)

    def check_health(self) -> tuple[bool, int, str]:
        if not self.api_key:
            return False, 0, "Gemini API key is not configured."
        start = time.perf_counter()
        try:
            url = f"{self.base_url}/models/{self.model_name}?key={self.api_key}"
            with httpx.Client(timeout=8.0) as client:
                res = client.get(url)
            latency_ms = max(1, int((time.perf_counter() - start) * 1000))
            if res.status_code == 200:
                return True, latency_ms, f"Gemini ({self.model_name}) online"
            return False, latency_ms, f"Gemini API returned HTTP {res.status_code}: {res.text[:100]}"
        except Exception as exc:
            return False, 0, f"Gemini connection failed: {exc}"


class OllamaLLMProvider(BaseLLMProvider):
    """
    Local Ollama integration for zero-cost offline development using Qwen3 4B.
    Runs on http://localhost:11434 with CPU or GPU inference.
    """

    provider_name: str = "ollama"

    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds or float(settings.OLLAMA_TIMEOUT_SECONDS)

    def generate_answer(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> LLMResponse:
        start_time = time.perf_counter()
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt,
            "options": {
                "temperature": temperature,
            },
            "stream": False,
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(url, json=payload)

            if res.status_code == 200:
                data = res.json()
                content = data.get("response", "")
                prompt_tokens = data.get("prompt_eval_count", len(prompt.split()))
                completion_tokens = data.get("eval_count", len(content.split()))
                latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))

                return LLMResponse(
                    content=content,
                    model=self.model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_ms=latency_ms,
                    provider="ollama",
                )

            if res.status_code == 404:
                raise RuntimeError(
                    f"Ollama model '{self.model_name}' not found. Please pull it locally using: 'ollama pull {self.model_name}'"
                )

            res.raise_for_status()

        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Ollama is unreachable at {self.base_url}. Ensure Ollama is installed and running ('ollama serve')."
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Ollama request timed out after {self.timeout_seconds}s during CPU inference. Consider increasing OLLAMA_TIMEOUT_SECONDS."
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Ollama generation failed: {exc}") from exc

        return LLMResponse(
            content=ABSTENTION_MESSAGE,
            model=self.model_name,
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=1,
            provider="ollama",
        )

    def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        schema_description: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        augmented_prompt = f"{prompt}\n\nOutput strictly valid JSON adhering to schema:\n{schema_description}"
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": augmented_prompt,
            "system": system_prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(url, json=payload)
            if res.status_code == 200:
                raw_json = res.json().get("response", "{}")
                return dict(json.loads(raw_json))
        except Exception:
            pass
        return {"status": "unparsed", "schema": schema_description}

    def summarize_document(self, text: str, max_tokens: int = 300) -> str:
        prompt = f"Summarize this clinical text in under {max_tokens} words:\n\n{text}"
        system = "You are an evidence-grounded medical summarizer."
        resp = self.generate_answer(prompt, system, temperature=0.0)
        return resp.content

    def extract_structured(self, text: str, target_schema: str) -> dict[str, Any]:
        prompt = f"Extract clinical entities from text:\n\n{text}"
        system = "Extract structured clinical data strictly as JSON."
        return self.generate_structured(prompt, system, target_schema, temperature=0.0)

    def check_health(self) -> tuple[bool, int, str]:
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
            latency_ms = max(1, int((time.perf_counter() - start) * 1000))
            if res.status_code == 200:
                models = [m.get("name", "") for m in res.json().get("models", [])]
                # Check for model match (e.g. qwen3:4b or qwen3:4b-latest)
                model_base = self.model_name.split(":")[0]
                has_model = any(model_base in m for m in models)
                if has_model:
                    return True, latency_ms, f"Ollama ({self.model_name}) online"
                return (
                    False,
                    latency_ms,
                    f"Ollama online, but model '{self.model_name}' missing. Run: 'ollama pull {self.model_name}'",
                )
            return False, latency_ms, f"Ollama returned HTTP {res.status_code}"
        except Exception as exc:
            return False, 0, f"Ollama unreachable at {self.base_url} ({exc})"


_llm_provider: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    """Returns singleton LLM provider instance configured by settings."""
    global _llm_provider
    if _llm_provider is None:
        provider_name = settings.LLM_PROVIDER.lower()

        if provider_name == "gemini":
            if settings.GEMINI_API_KEY:
                logger.info("Initializing GeminiLLMProvider with model '%s'", settings.GEMINI_MODEL)
                _llm_provider = GeminiLLMProvider()
            elif settings.ENVIRONMENT == "production" and not settings.ALLOW_MOCK_IN_PRODUCTION:
                raise ConfigurationError(
                    "GEMINI_API_KEY is not configured in production environment. Mock fallback is strictly prohibited."
                )
            elif settings.LLM_FALLBACK_TO_MOCK:
                logger.warning("GEMINI_API_KEY is not set. Falling back to MockLLMProvider.")
                _llm_provider = MockLLMProvider()
            else:
                _llm_provider = GeminiLLMProvider()

        elif provider_name == "ollama":
            logger.info("Initializing OllamaLLMProvider at %s with model '%s'", settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL)
            _llm_provider = OllamaLLMProvider()

        elif provider_name == "mock":
            if settings.ENVIRONMENT == "production" and not settings.ALLOW_MOCK_IN_PRODUCTION:
                raise ConfigurationError(
                    "MockLLMProvider is strictly prohibited when ENVIRONMENT=production."
                )
            logger.info("Using default MockLLMProvider.")
            _llm_provider = MockLLMProvider()

        else:
            if settings.ENVIRONMENT == "production" and not settings.ALLOW_MOCK_IN_PRODUCTION:
                raise ConfigurationError(
                    f"Unsupported LLM provider '{provider_name}' in production environment."
                )
            logger.info("Using default MockLLMProvider for unknown provider '%s'.", provider_name)
            _llm_provider = MockLLMProvider()

    return _llm_provider


def reset_llm_provider() -> None:
    """Resets the singleton provider, allowing test fixtures to reconfigure providers dynamically."""
    global _llm_provider
    _llm_provider = None
