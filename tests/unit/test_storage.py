"""Unit tests for document storage adapter and PDF validation."""

from pathlib import Path

import pytest

from backend.documents.storage import DocumentStorage
from backend.documents.validator import validate_pdf_file


def test_validate_valid_pdf_file() -> None:
    """Verifies that a file with %PDF- header passes validation."""
    content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    is_valid, file_hash, err = validate_pdf_file(content, filename="report.pdf")
    assert is_valid is True
    assert len(file_hash) == 64
    assert err == ""


def test_validate_rejects_non_pdf_file() -> None:
    """Verifies that files without PDF magic bytes are rejected."""
    content = b"<html><body>Not a PDF</body></html>"
    is_valid, file_hash, err = validate_pdf_file(content, filename="fake.pdf")
    assert is_valid is False
    assert "magic bytes" in err


def test_validate_rejects_oversized_file() -> None:
    """Verifies that files exceeding max size are rejected."""
    content = b"%PDF-1.4" + b"X" * 1024
    # Max size = 0 MB (0 bytes allowed)
    is_valid, file_hash, err = validate_pdf_file(content, max_size_mb=0)
    assert is_valid is False
    assert "exceeds maximum permitted limit" in err


def test_document_storage_save_and_read(tmp_path: Path) -> None:
    """Verifies saving and reading back file bytes using DocumentStorage."""
    storage = DocumentStorage(base_dir=tmp_path)
    sample_content = b"%PDF-1.5 test document content"
    sample_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    rel_path = storage.save_file(sample_content, sample_hash)
    assert rel_path == f"{sample_hash[:2]}/{sample_hash}.pdf"
    assert storage.exists(rel_path) is True

    read_back = storage.read_file(rel_path)
    assert read_back == sample_content

    deleted = storage.delete_file(rel_path)
    assert deleted is True
    assert storage.exists(rel_path) is False


def test_document_storage_path_traversal_protection(tmp_path: Path) -> None:
    """Verifies that path traversal attempts raise ValueError."""
    storage = DocumentStorage(base_dir=tmp_path)
    with pytest.raises(ValueError, match="Path traversal"):
        storage.get_absolute_path("../../etc/passwd")
