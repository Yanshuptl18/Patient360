"""Unit tests for OCR pipeline, scanned PDF detection, image preprocessing, and CER/WER."""

import io

import pymupdf
from PIL import Image, ImageDraw

from backend.ingestion.extractor import extract_pages_from_pdf
from backend.ingestion.ocr import (
    calculate_cer,
    calculate_wer,
    is_page_scanned,
    preprocess_scanned_image,
    render_page_to_image,
)


def create_scanned_image_page_pdf() -> bytes:
    """Generates a synthetic PDF where page 1 is a scanned image with medical values."""
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "DISCHARGE MEDICAL SUMMARY", fill=(0, 0, 0))
    draw.text((50, 100), "Patient: Eleanor Vance", fill=(0, 0, 0))
    draw.text((50, 150), "Prescription: Lisinopril 20mg PO once daily", fill=(0, 0, 0))
    draw.text((50, 200), "Blood Pressure: 130/85 mmHg", fill=(0, 0, 0))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    rect = pymupdf.Rect(0, 0, 600, 800)
    page.insert_image(rect, stream=img_bytes)

    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def create_mixed_pdf() -> bytes:
    """Generates a 2-page PDF: page 1 is native text, page 2 is a scanned image."""
    doc = pymupdf.open()

    # Page 1: Native digital text
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 72), "CLINICAL PROGRESS NOTE\nPatient has stable cardiopulmonary status.", fontsize=12)

    # Page 2: Scanned lab report image
    img = Image.new("RGB", (595, 842), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "LABORATORY PANEL\nPotassium: 4.2 mEq/L\nSodium: 140 mEq/L", fill=(0, 0, 0))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    p2 = doc.new_page(width=595, height=842)
    p2.insert_image(pymupdf.Rect(0, 0, 595, 842), stream=img_bytes)

    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_scanned_page_detection() -> None:
    """Verifies that an image-only PDF page with zero text is detected as scanned."""
    pdf_bytes = create_scanned_image_page_pdf()
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[0]
        assert is_page_scanned(page) is True
    finally:
        doc.close()


def test_image_preprocessing_pipeline() -> None:
    """Verifies that grayscale, contrast stretching, and binarization execute cleanly."""
    raw_img = Image.new("RGB", (200, 200), color=(200, 150, 100))
    processed = preprocess_scanned_image(raw_img)
    assert processed.mode == "L"
    assert processed.size == (200, 200)


def test_render_page_to_image() -> None:
    """Verifies page rasterization with high DPI."""
    pdf_bytes = create_scanned_image_page_pdf()
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[0]
        rendered = render_page_to_image(page, dpi=150)
        assert isinstance(rendered, Image.Image)
        assert rendered.width > 0
        assert rendered.height > 0
    finally:
        doc.close()


def test_mixed_pdf_extraction() -> None:
    """Verifies extraction preserves physical page numbers across mixed text/scanned pages."""
    pdf_bytes = create_mixed_pdf()
    extracted_pages = extract_pages_from_pdf(pdf_bytes)

    assert len(extracted_pages) == 2
    assert extracted_pages[0].page_number == 1
    assert "CLINICAL PROGRESS NOTE" in extracted_pages[0].text
    assert extracted_pages[0].is_ocr is False

    assert extracted_pages[1].page_number == 2
    assert extracted_pages[1].is_ocr is True
    assert extracted_pages[1].ocr_confidence > 0.0


def test_cer_and_wer_metrics() -> None:
    """Verifies mathematical CER and WER calculation."""
    ref = "Metformin 500mg orally once daily"
    hyp_identical = "Metformin 500mg orally once daily"
    assert calculate_cer(ref, hyp_identical) == 0.0
    assert calculate_wer(ref, hyp_identical) == 0.0

    hyp_one_word_error = "Metformin 1000mg orally once daily"
    wer = calculate_wer(ref, hyp_one_word_error)
    assert 0.15 <= wer <= 0.25

    cer = calculate_cer(ref, hyp_one_word_error)
    assert cer > 0.0
