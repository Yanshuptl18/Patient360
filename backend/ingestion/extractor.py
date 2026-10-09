"""PyMuPDF page-aware document text and layout block extractor."""

import logging
from dataclasses import dataclass, field
from typing import Any

import pymupdf

from backend.core.exceptions import Patient360Exception

logger = logging.getLogger(__name__)


@dataclass
class ExtractedPage:
    """Represents text and layout blocks extracted from a physical PDF page."""

    page_number: int  # 1-indexed physical page number
    text: str
    blocks: list[dict[str, Any]] = field(default_factory=list)
    is_blank: bool = False


def extract_pages_from_pdf(pdf_bytes: bytes) -> list[ExtractedPage]:
    """
    Extracts text page-by-page from raw PDF bytes using PyMuPDF.
    Preserves exact physical page numbers and block bounding boxes.

    Raises Patient360Exception if document parsing fails or bytes are corrupt.
    """
    if not pdf_bytes:
        raise Patient360Exception(
            message="Cannot extract text from empty document payload.",
            code="EMPTY_PAYLOAD",
            status_code=400,
        )

    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as err:
        logger.error(f"Failed to open PDF stream with PyMuPDF: {err}")
        raise Patient360Exception(
            message=f"Failed to parse PDF document structure: {err}",
            code="PDF_PARSING_FAILED",
            status_code=400,
        ) from err

    extracted_pages: list[ExtractedPage] = []

    try:
        total_pages = len(doc)
        if total_pages == 0:
            raise Patient360Exception(
                message="PDF contains zero document pages.",
                code="ZERO_PAGES",
                status_code=400,
            )

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_number = page_idx + 1  # 1-indexed

            # Extract layout blocks: (x0, y0, x1, y1, text, block_no, block_type)
            # block_type 0 is text, block_type 1 is image
            raw_blocks = page.get_text("blocks")
            text_blocks: list[dict[str, Any]] = []
            page_text_parts: list[str] = []

            for blk in raw_blocks:
                if len(blk) >= 7 and blk[6] == 0:  # Text block
                    bbox = [round(blk[0], 2), round(blk[1], 2), round(blk[2], 2), round(blk[3], 2)]
                    block_text = blk[4].strip()
                    if block_text:
                        text_blocks.append(
                            {
                                "block_index": blk[5],
                                "bbox": bbox,
                                "text": block_text,
                            }
                        )
                        page_text_parts.append(block_text)

            full_page_text = "\n\n".join(page_text_parts).strip()
            is_blank = len(full_page_text) < 5

            extracted_pages.append(
                ExtractedPage(
                    page_number=page_number,
                    text=full_page_text,
                    blocks=text_blocks,
                    is_blank=is_blank,
                )
            )

        logger.info(f"Successfully extracted {len(extracted_pages)} pages from PDF.")
        return extracted_pages
    finally:
        doc.close()
