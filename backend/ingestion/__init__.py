"""Document ingestion, PyMuPDF extraction, clinical normalization, and semantic chunking."""

from backend.ingestion.chunker import SemanticChunker
from backend.ingestion.extractor import ExtractedPage, extract_pages_from_pdf
from backend.ingestion.normalizer import normalize_clinical_text
from backend.ingestion.service import ingest_document

__all__ = [
    "ExtractedPage",
    "extract_pages_from_pdf",
    "normalize_clinical_text",
    "SemanticChunker",
    "ingest_document",
]
