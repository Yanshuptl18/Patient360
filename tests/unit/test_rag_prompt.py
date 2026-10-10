"""Unit tests for GroundedPromptBuilder context assembly and security boundaries."""

from backend.rag.prompt import GroundedPromptBuilder
from backend.vector.store import VectorSearchResult


def test_grounded_prompt_builder_format() -> None:
    """Verifies that untrusted document delimiters and citation markers are injected properly."""
    builder = GroundedPromptBuilder(max_context_tokens=1000)

    chunks = [
        VectorSearchResult(
            chunk_id="chk-1",
            document_id="doc-101",
            patient_id="pat-1",
            page_number=1,
            chunk_index=0,
            content="[Document: Consultation | Page: 1] Patient reports shortness of breath.",
            raw_content="Patient reports shortness of breath.",
            score=0.88,
            doc_title="Consultation_Report.pdf",
            doc_type="patient_record",
            doc_date="2024-03-15",
        ),
        VectorSearchResult(
            chunk_id="chk-2",
            document_id="doc-102",
            patient_id="pat-1",
            page_number=3,
            chunk_index=1,
            content="[Document: Pathology | Page: 3] Adenocarcinoma positive for EGFR L858R.",
            raw_content="Adenocarcinoma positive for EGFR L858R.",
            score=0.92,
            doc_title="Pathology_Report.pdf",
            doc_type="lab_report",
            doc_date="2024-03-18",
        ),
    ]

    prompt = builder.build_prompt(
        query="What molecular alterations were identified?",
        retrieved_chunks=chunks,
    )

    assert "=== BEGIN VERIFIED DOCUMENT PASSAGES ===" in prompt
    assert "=== END VERIFIED DOCUMENT PASSAGES ===" in prompt
    assert "<<<UNTRUSTED_DOCUMENT_CONTENT [Doc: doc-101, Page: 1]>>>" in prompt
    assert "<<<UNTRUSTED_DOCUMENT_CONTENT [Doc: doc-102, Page: 3]>>>" in prompt
    assert "Clinical Inquiry: What molecular alterations were identified?" in prompt
    assert "Synthesized Answer:" in prompt


def test_grounded_prompt_builder_token_truncation() -> None:
    """Verifies that chunks exceeding the token budget are not included."""
    # Set a tiny token limit of 15 tokens
    builder = GroundedPromptBuilder(max_context_tokens=15)

    chunks = [
        VectorSearchResult(
            chunk_id="chk-1",
            document_id="doc-101",
            patient_id="pat-1",
            page_number=1,
            chunk_index=0,
            content="Short first sentence here.",
            raw_content="Short first sentence here.",
            score=0.88,
            doc_title="Doc1.pdf",
            doc_type="patient_record",
            doc_date="2024-03-15",
        ),
        VectorSearchResult(
            chunk_id="chk-2",
            document_id="doc-102",
            patient_id="pat-1",
            page_number=2,
            chunk_index=1,
            content="This is a very long second passage with lots of text that definitely exceeds the remaining token allocation budget.",
            raw_content="This is a very long second passage...",
            score=0.85,
            doc_title="Doc2.pdf",
            doc_type="lab_report",
            doc_date="2024-03-18",
        ),
        VectorSearchResult(
            chunk_id="chk-3",
            document_id="doc-103",
            patient_id="pat-1",
            page_number=3,
            chunk_index=2,
            content="Third passage that should be completely skipped.",
            raw_content="Third passage...",
            score=0.80,
            doc_title="Doc3.pdf",
            doc_type="lab_report",
            doc_date="2024-03-19",
        ),
    ]

    prompt = builder.build_prompt(query="Test query", retrieved_chunks=chunks)
    assert "[Doc: doc-101, Page: 1]" in prompt
    assert "[Doc: doc-103, Page: 3]" not in prompt
