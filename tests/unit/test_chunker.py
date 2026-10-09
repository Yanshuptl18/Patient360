"""Unit tests for semantic chunker and page attribution."""

from backend.ingestion.chunker import SemanticChunker
from backend.ingestion.extractor import ExtractedPage


def test_chunker_preserves_100_percent_page_numbers() -> None:
    """Verifies that every generated chunk retains accurate page numbers across multi-page input."""
    pages = [
        ExtractedPage(page_number=1, text="Page 1 sentence one. Page 1 sentence two."),
        ExtractedPage(page_number=2, text="Page 2 findings. Page 2 laboratory results."),
        ExtractedPage(page_number=3, text="Page 3 discharge plan and follow-up."),
    ]
    chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_pages(
        pages=pages,
        doc_title="Clinical Note",
        doc_date="2024-03-15",
        doc_type="patient_record",
        patient_id="patient-123",
    )

    assert len(chunks) == 3
    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2
    assert chunks[2].page_number == 3

    for i, c in enumerate(chunks):
        assert c.chunk_index == i
        assert c.metadata["page_number"] == c.page_number
        assert c.metadata["patient_id"] == "patient-123"
        assert c.token_count > 0


def test_chunker_injects_context_header() -> None:
    """Verifies context header injection format as specified in RAG_DESIGN.md."""
    pages = [ExtractedPage(page_number=1, text="Primary diagnosis is glioblastoma multiforme.")]
    chunker = SemanticChunker()
    chunks = chunker.chunk_pages(
        pages=pages,
        doc_title="Oncology Consult",
        doc_date="2024-04-10",
        doc_type="patient_record",
    )

    assert len(chunks) == 1
    expected_header = "[Document: Oncology Consult | Page: 1 | Date: 2024-04-10]\n"
    assert chunks[0].content.startswith(expected_header)
    assert "Primary diagnosis is glioblastoma multiforme." in chunks[0].content
    assert chunks[0].raw_content == "Primary diagnosis is glioblastoma multiforme."


def test_chunker_does_not_split_decimals_or_abbreviations() -> None:
    """Verifies that sentence splitting avoids splitting inside decimals or abbreviations."""
    pages = [
        ExtractedPage(
            page_number=1,
            text="Administer 0.5 mg morphine p.r.n. pain. Patient tolerating oral intake well.",
        )
    ]
    chunker = SemanticChunker(chunk_size=20, chunk_overlap=5)
    chunks = chunker.chunk_pages(pages=pages, doc_title="Nursing Note")

    # "0.5 mg" and "p.r.n." should be intact
    assert any("0.5 mg morphine p.r.n. pain" in c.raw_content for c in chunks)
