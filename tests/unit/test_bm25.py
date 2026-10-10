"""Unit tests for in-memory BM25 sparse keyword retriever and clinical tokenization."""

from backend.retrieval.bm25 import (
    BM25Document,
    BM25Index,
    PatientBM25Registry,
    tokenize_clinical_text,
)


def test_clinical_tokenization_preserves_acronyms_and_hyphens() -> None:
    """Verifies that clinical acronyms, gene variants, and hyphens are preserved."""
    sample = "Patient diagnosed with COVID-19, EGFR-mutated L858R, and elevated NT-proBNP."
    tokens = tokenize_clinical_text(sample)

    assert "covid-19" in tokens
    assert "egfr-mutated" in tokens
    assert "l858r" in tokens
    assert "nt-probnp" in tokens


def test_bm25_index_and_exact_keyword_search() -> None:
    """Verifies that Okapi BM25 accurately scores and ranks exact keyword matches."""
    index = BM25Index()

    docs = [
        BM25Document(
            chunk_id="chk-1",
            document_id="doc-1",
            patient_id="pat-1",
            page_number=1,
            chunk_index=0,
            content="Patient presents with severe dyspnea and persistent cough.",
            raw_content="Patient presents with severe dyspnea and persistent cough.",
            doc_title="Consult.pdf",
            doc_type="patient_record",
            doc_date="2024-03-01",
        ),
        BM25Document(
            chunk_id="chk-2",
            document_id="doc-2",
            patient_id="pat-1",
            page_number=2,
            chunk_index=1,
            content="Molecular diagnostics identified an EGFR L858R point mutation in exon 21.",
            raw_content="Molecular diagnostics identified an EGFR L858R point mutation in exon 21.",
            doc_title="Biopsy.pdf",
            doc_type="lab_report",
            doc_date="2024-03-05",
        ),
        BM25Document(
            chunk_id="chk-3",
            document_id="doc-3",
            patient_id="pat-1",
            page_number=1,
            chunk_index=2,
            content="Laboratory panel showed NT-proBNP 4200 pg/mL indicating heart failure.",
            raw_content="Laboratory panel showed NT-proBNP 4200 pg/mL indicating heart failure.",
            doc_title="Labs.pdf",
            doc_type="lab_report",
            doc_date="2024-03-06",
        ),
    ]

    index.index_documents(docs)

    # Search for rare abbreviation: NT-proBNP
    results = index.search("NT-proBNP", top_k=5)
    assert len(results) == 1
    assert results[0].chunk_id == "chk-3"
    assert results[0].score > 0.0

    # Search for gene mutation: L858R
    results_gene = index.search("L858R mutation", top_k=5)
    assert len(results_gene) >= 1
    assert results_gene[0].chunk_id == "chk-2"


def test_patient_bm25_registry_tenant_isolation() -> None:
    """Verifies that patient indexes are partitioned and strictly isolated."""
    registry = PatientBM25Registry()

    doc_patient_a = BM25Document(
        chunk_id="chk-a",
        document_id="doc-a",
        patient_id="pat-a",
        page_number=1,
        chunk_index=0,
        content="Patient Alice has confirmed adenocarcinoma.",
        raw_content="Patient Alice has confirmed adenocarcinoma.",
        doc_title="Alice.pdf",
        doc_type="patient_record",
        doc_date="2024-01-01",
    )

    doc_patient_b = BM25Document(
        chunk_id="chk-b",
        document_id="doc-b",
        patient_id="pat-b",
        page_number=1,
        chunk_index=0,
        content="Patient Bob has confirmed glioblastoma.",
        raw_content="Patient Bob has confirmed glioblastoma.",
        doc_title="Bob.pdf",
        doc_type="patient_record",
        doc_date="2024-01-02",
    )

    registry.index_chunks("pat-a", [doc_patient_a])
    registry.index_chunks("pat-b", [doc_patient_b])

    # Search within Patient A index: glioblastoma must NOT appear
    results_a = registry.get_index_for_patient("pat-a").search("glioblastoma")
    assert len(results_a) == 0

    # Search within Patient B index: adenocarcinoma must NOT appear
    results_b = registry.get_index_for_patient("pat-b").search("adenocarcinoma")
    assert len(results_b) == 0


def test_bm25_document_deletion() -> None:
    """Verifies that deleted document chunks are removed from search results."""
    index = BM25Index()

    docs = [
        BM25Document(
            chunk_id="chk-10",
            document_id="doc-to-delete",
            patient_id="pat-1",
            page_number=1,
            chunk_index=0,
            content="Sensitive clinical finding to delete.",
            raw_content="Sensitive clinical finding to delete.",
            doc_title="DeleteMe.pdf",
            doc_type="patient_record",
            doc_date="2024-02-01",
        )
    ]
    index.index_documents(docs)
    assert len(index.search("Sensitive")) == 1

    index.delete_document_chunks("doc-to-delete")
    assert len(index.search("Sensitive")) == 0
