"""Unit tests for CitationVerifier parsing, exact quote mapping, and claim verification."""

from backend.rag.citations import CitationVerifier
from backend.vector.store import VectorSearchResult


def test_citation_verifier_supported_citation() -> None:
    """Verifies that citations matching retrieved passages are extracted and marked 'supported'."""
    verifier = CitationVerifier()

    chunks = [
        VectorSearchResult(
            chunk_id="chk-1",
            document_id="doc-99",
            patient_id="pat-1",
            page_number=2,
            chunk_index=0,
            content="[Document: Pathology] Biopsy confirmed invasive lung adenocarcinoma with EGFR L858R.",
            raw_content="Biopsy confirmed invasive lung adenocarcinoma with EGFR L858R.",
            score=0.91,
            doc_title="Molecular_Pathology.pdf",
            doc_type="lab_report",
            doc_date="2024-03-18",
        )
    ]

    answer = (
        "Invasive lung adenocarcinoma harboring an EGFR L858R point mutation was confirmed by biopsy "
        "[Doc: doc-99, Page 2]."
    )

    citations, is_abstention = verifier.verify(answer=answer, retrieved_chunks=chunks)

    assert not is_abstention
    assert len(citations) == 1
    c = citations[0]
    assert c.document_id == "doc-99"
    assert c.page_number == 2
    assert c.document_title == "Molecular_Pathology.pdf"
    assert c.verification_status == "supported"
    assert "Biopsy confirmed invasive lung adenocarcinoma" in c.exact_quote


def test_citation_verifier_unsupported_citation() -> None:
    """Verifies that fabricated or hallucinated citations are flagged as 'unsupported'."""
    verifier = CitationVerifier()

    chunks = [
        VectorSearchResult(
            chunk_id="chk-1",
            document_id="doc-99",
            patient_id="pat-1",
            page_number=1,
            chunk_index=0,
            content="General vital signs were normal.",
            raw_content="General vital signs were normal.",
            score=0.70,
            doc_title="Vitals.pdf",
            doc_type="patient_record",
            doc_date="2024-03-10",
        )
    ]

    # Model hallucinates a citation to a non-existent document
    answer = "Patient had a severe reaction to penicillin [Doc: non-existent-doc, Page 99]."
    citations, is_abstention = verifier.verify(answer=answer, retrieved_chunks=chunks)

    assert not is_abstention
    assert len(citations) == 1
    assert citations[0].verification_status == "unsupported"


def test_citation_verifier_abstention_detection() -> None:
    """Verifies that standard abstention statements return is_abstention=True and empty citations."""
    verifier = CitationVerifier()

    answer = "Insufficient evidence documented in available records."
    citations, is_abstention = verifier.verify(answer=answer, retrieved_chunks=[])

    assert is_abstention
    assert len(citations) == 0
