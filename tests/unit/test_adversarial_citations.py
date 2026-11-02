"""Unit tests for adversarial citation scenarios, polarity inversion, and numeric hallucination."""

from backend.rag.citations import CitationVerifier
from backend.vector.store import VectorSearchResult


def test_polarity_inversion_detected_as_unsupported() -> None:
    """Verifies that an affirmative claim citing a negated passage is flagged as unsupported."""
    verifier = CitationVerifier()
    chunks = [
        VectorSearchResult(
            chunk_id="chk-1",
            document_id="doc-101",
            patient_id="pat-1",
            page_number=1,
            chunk_index=0,
            content="Cardiology note: Patient denies chest pain or shortness of breath on exertion.",
            raw_content="Patient denies chest pain or shortness of breath on exertion.",
            score=0.88,
            doc_title="Cardiology_Consult.pdf",
            doc_type="clinical_note",
            doc_date="2024-04-01",
        )
    ]

    # Adversarial claim: asserts chest pain when source states denies chest pain
    answer = "The patient presented with recurrent chest pain on exertion [Doc: doc-101, Page 1]."
    citations, is_abstention = verifier.verify(answer=answer, retrieved_chunks=chunks)

    assert not is_abstention
    assert len(citations) == 1
    assert citations[0].verification_status == "unsupported"


def test_reverse_polarity_inversion_detected_as_unsupported() -> None:
    """Verifies that a negated claim citing an affirmative passage is flagged as unsupported."""
    verifier = CitationVerifier()
    chunks = [
        VectorSearchResult(
            chunk_id="chk-2",
            document_id="doc-102",
            patient_id="pat-1",
            page_number=3,
            chunk_index=1,
            content="Pathology report: Biopsy confirmed invasive adenocarcinoma with positive margins.",
            raw_content="Biopsy confirmed invasive adenocarcinoma with positive margins.",
            score=0.92,
            doc_title="Pathology.pdf",
            doc_type="pathology_report",
            doc_date="2024-04-02",
        )
    ]

    # Adversarial claim: asserts no adenocarcinoma when source confirms it
    answer = "Biopsy revealed no adenocarcinoma in the tissue samples [Doc: doc-102, Page 3]."
    citations, is_abstention = verifier.verify(answer=answer, retrieved_chunks=chunks)

    assert not is_abstention
    assert len(citations) == 1
    assert citations[0].verification_status == "unsupported"


def test_polarity_agreement_negation_supported() -> None:
    """Verifies that when both claim and passage express negation, claim is verified as supported."""
    verifier = CitationVerifier()
    chunks = [
        VectorSearchResult(
            chunk_id="chk-3",
            document_id="doc-103",
            patient_id="pat-1",
            page_number=1,
            chunk_index=0,
            content="Patient denies any prior history of diabetes mellitus or hypertension.",
            raw_content="Patient denies any prior history of diabetes mellitus or hypertension.",
            score=0.85,
            doc_title="Admission_H_and_P.pdf",
            doc_type="clinical_note",
            doc_date="2024-04-05",
        )
    ]

    answer = "Patient denies any prior history of diabetes mellitus [Doc: doc-103, Page 1]."
    citations, is_abstention = verifier.verify(answer=answer, retrieved_chunks=chunks)

    assert not is_abstention
    assert len(citations) == 1
    assert citations[0].verification_status == "supported"


def test_numeric_dosage_discrepancy_downgraded() -> None:
    """Verifies that fabricated or mismatched dosages are downgraded to partially_supported."""
    verifier = CitationVerifier()
    chunks = [
        VectorSearchResult(
            chunk_id="chk-4",
            document_id="doc-104",
            patient_id="pat-1",
            page_number=2,
            chunk_index=0,
            content="Prescriptions: Patient was started on Metformin 500mg orally once daily.",
            raw_content="Patient was started on Metformin 500mg orally once daily.",
            score=0.89,
            doc_title="Prescriptions.pdf",
            doc_type="prescription",
            doc_date="2024-04-10",
        )
    ]

    # Hallucinated dose: 1000mg instead of 500mg
    answer = "Patient was prescribed Metformin 1000mg orally once daily [Doc: doc-104, Page 2]."
    citations, is_abstention = verifier.verify(answer=answer, retrieved_chunks=chunks)

    assert not is_abstention
    assert len(citations) == 1
    assert citations[0].verification_status == "partially_supported"


def test_numeric_dosage_match_supported() -> None:
    """Verifies that matching dosages and numbers remain fully supported."""
    verifier = CitationVerifier()
    chunks = [
        VectorSearchResult(
            chunk_id="chk-5",
            document_id="doc-105",
            patient_id="pat-1",
            page_number=1,
            chunk_index=0,
            content="Vital signs: Blood pressure was 120/80 mmHg and heart rate was 72 bpm.",
            raw_content="Blood pressure was 120/80 mmHg and heart rate was 72 bpm.",
            score=0.90,
            doc_title="Vitals.pdf",
            doc_type="clinical_note",
            doc_date="2024-04-12",
        )
    ]

    answer = "Recorded blood pressure was 120/80 mmHg with heart rate 72 bpm [Doc: doc-105, Page 1]."
    citations, is_abstention = verifier.verify(answer=answer, retrieved_chunks=chunks)

    assert not is_abstention
    assert len(citations) == 1
    assert citations[0].verification_status == "supported"

