"""Unit tests for MockLLMProvider evidence grounding and deterministic abstention."""

from backend.rag.llm import MockLLMProvider


def test_mock_llm_provider_evidence_grounded_answer() -> None:
    """Verifies that MockLLMProvider synthesizes an answer with citations when facts are present."""
    provider = MockLLMProvider()

    prompt = (
        "=== BEGIN VERIFIED DOCUMENT PASSAGES ===\n"
        "<<<UNTRUSTED_DOCUMENT_CONTENT [Doc: doc-alpha-123, Page: 2]>>>\n"
        "Findings: Molecular testing identified EGFR L858R mutation in exon 21.\n"
        "<<<END_UNTRUSTED_DOCUMENT_CONTENT>>>\n"
        "=== END VERIFIED DOCUMENT PASSAGES ===\n\n"
        "Clinical Inquiry: What EGFR mutation was found?\n"
        "Synthesized Answer:"
    )

    response = provider.generate_answer(prompt=prompt, system_prompt="You are a clinical assistant.")

    assert "EGFR" in response.content
    assert "[Doc: doc-alpha-123, Page: 2]" in response.content
    assert response.completion_tokens > 0
    assert response.latency_ms >= 1


def test_mock_llm_provider_abstention_on_unmentioned_inquiry() -> None:
    """Verifies that MockLLMProvider returns standard abstention when inquiry is absent in passages."""
    provider = MockLLMProvider()

    prompt = (
        "=== BEGIN VERIFIED DOCUMENT PASSAGES ===\n"
        "<<<UNTRUSTED_DOCUMENT_CONTENT [Doc: doc-beta-456, Page: 1]>>>\n"
        "Patient Eleanor Vance presented with dry cough and mild fatigue.\n"
        "<<<END_UNTRUSTED_DOCUMENT_CONTENT>>>\n"
        "=== END VERIFIED DOCUMENT PASSAGES ===\n\n"
        "Clinical Inquiry: Does this patient have documented penicillin anaphylaxis?\n"
        "Synthesized Answer:"
    )

    response = provider.generate_answer(prompt=prompt, system_prompt="You are a clinical assistant.")

    assert "Insufficient evidence documented in available records." in response.content
