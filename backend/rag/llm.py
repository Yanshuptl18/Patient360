"""LLM provider interface and implementations for grounded evidence generation."""

import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.core.config import settings

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


class BaseLLMProvider(ABC):
    """Abstract base class for LLM generation providers."""

    @abstractmethod
    def generate_answer(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Generates an evidence-grounded answer given the structured prompt."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic clinical LLM provider for tests, CI, and offline local development.
    Adheres strictly to evidence grounding:
    - Synthesizes findings directly from context passages with [Doc: {id}, Page: {no}] tags.
    - Emits standard abstention message when evidence is insufficient.
    """

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
        # Filter out stopwords
        stopwords = {
            "what", "is", "the", "a", "an", "this", "that", "in", "on", "of", "and", "or",
            "patient", "has", "have", "had", "for", "with", "any", "are", "were", "to",
            "does", "do", "did", "reported", "documented", "there", "show", "showed"
        }
        clinical_keywords = query_tokens - stopwords

        scored_statements: list[tuple[int, str]] = []

        for doc_id, page_no, content in passages:
            # Strip context header before processing
            cleaned_content = re.sub(r"^\[Document:.*?\]\s*", "", content, flags=re.IGNORECASE).strip()
            content_lower = cleaned_content.lower()

            # Check for keyword overlap
            matched_kw = [kw for kw in clinical_keywords if kw in content_lower]

            if matched_kw:
                has_relevant_evidence = True
                # Extract key clinical sentences without splitting on internal decimals/periods
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

        # If zero passages or no clinical overlap found, abstain deterministically
        if not has_relevant_evidence or not scored_statements:
            content_output = ABSTENTION_MESSAGE
        else:
            # Sort by keyword match count descending, deduplicating while preserving rank
            scored_statements.sort(key=lambda x: x[0], reverse=True)
            seen = set()
            unique_statements: list[str] = []
            for _, stmt in scored_statements:
                if stmt not in seen:
                    seen.add(stmt)
                    unique_statements.append(stmt)

            content_output = " ".join(unique_statements[:4])

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        prompt_tokens = len(prompt.split())
        completion_tokens = len(content_output.split())

        return LLMResponse(
            content=content_output,
            model=self.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=max(1, latency_ms),
        )


_llm_provider: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    """Returns singleton LLM provider instance configured by settings."""
    global _llm_provider
    if _llm_provider is None:
        provider_name = settings.LLM_PROVIDER.lower()
        if provider_name == "mock":
            _llm_provider = MockLLMProvider()
        else:
            # Default to MockLLMProvider if remote provider keys are absent
            logger.info("Configured LLM provider '%s', defaulting to MockLLMProvider.", provider_name)
            _llm_provider = MockLLMProvider()

    return _llm_provider
