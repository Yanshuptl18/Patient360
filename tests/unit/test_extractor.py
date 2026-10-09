"""Unit tests for PyMuPDF page-aware PDF extraction."""

import pymupdf
import pytest

from backend.core.exceptions import Patient360Exception
from backend.ingestion.extractor import extract_pages_from_pdf


def create_test_pdf_bytes(page_texts: list[str]) -> bytes:
    """Helper to generate a real multi-page PDF in memory using PyMuPDF."""
    doc = pymupdf.open()
    for text in page_texts:
        page = doc.new_page(width=595, height=842)  # Standard A4
        if text.strip():
            page.insert_text((50, 72), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_extract_pages_from_multipage_pdf() -> None:
    """Verifies that multi-page PDFs extract each physical page with accurate 1-indexed page numbers."""
    pages_content = [
        "Patient Eleanor Vance presented on 2024-03-15 with persistent dyspnea.",
        "Pathology Report: Poorly differentiated adenocarcinoma with EGFR L858R mutation.",
        "Clinical plan: Initiate Osimertinib 80 mg p.o. once daily with follow-up in 4 weeks.",
    ]
    pdf_bytes = create_test_pdf_bytes(pages_content)

    extracted = extract_pages_from_pdf(pdf_bytes)

    assert len(extracted) == 3
    assert extracted[0].page_number == 1
    assert "Eleanor Vance" in extracted[0].text
    assert not extracted[0].is_blank

    assert extracted[1].page_number == 2
    assert "Pathology Report" in extracted[1].text
    assert "EGFR L858R" in extracted[1].text
    assert not extracted[1].is_blank

    assert extracted[2].page_number == 3
    assert "Osimertinib 80 mg" in extracted[2].text
    assert not extracted[2].is_blank


def test_extract_pages_with_blank_page() -> None:
    """Verifies that blank pages are flagged properly."""
    pdf_bytes = create_test_pdf_bytes(["Header on page 1", "   ", "Content on page 3"])
    extracted = extract_pages_from_pdf(pdf_bytes)

    assert len(extracted) == 3
    assert not extracted[0].is_blank
    assert extracted[1].is_blank
    assert extracted[1].page_number == 2
    assert not extracted[2].is_blank
    assert extracted[2].page_number == 3


def test_extract_pages_block_metadata() -> None:
    """Verifies layout block bounding coordinates are populated."""
    pdf_bytes = create_test_pdf_bytes(["Line 1\nLine 2 in block"])
    extracted = extract_pages_from_pdf(pdf_bytes)

    assert len(extracted) == 1
    assert len(extracted[0].blocks) >= 1
    blk = extracted[0].blocks[0]
    assert "bbox" in blk
    assert len(blk["bbox"]) == 4
    assert "text" in blk
    assert "Line 1" in blk["text"]


def test_extract_empty_or_corrupt_payload() -> None:
    """Verifies rejection of empty or non-PDF bytes."""
    with pytest.raises(Patient360Exception) as exc_info:
        extract_pages_from_pdf(b"")
    assert exc_info.value.code == "EMPTY_PAYLOAD"

    with pytest.raises(Patient360Exception) as exc_info2:
        extract_pages_from_pdf(b"not a valid pdf binary content")
    assert exc_info2.value.code == "PDF_PARSING_FAILED"
