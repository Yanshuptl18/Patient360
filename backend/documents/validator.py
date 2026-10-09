"""PDF document validation: magic bytes, size limits, and cryptographic hashing."""

import hashlib

from backend.core.config import settings


def calculate_sha256(content: bytes) -> str:
    """Calculates the SHA-256 hexadecimal digest for raw file bytes."""
    return hashlib.sha256(content).hexdigest()


def validate_pdf_file(
    content: bytes,
    filename: str = "",
    max_size_mb: int = settings.MAX_UPLOAD_SIZE_MB,
) -> tuple[bool, str, str]:
    """
    Validates uploaded file against security constraints:
    1. Maximum file size (default 25 MB).
    2. Magic bytes verification (must begin with %PDF-).
    3. Computes SHA-256 hash.

    Returns: (is_valid, sha256_hash, error_message)
    """
    max_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        return (
            False,
            "",
            f"File size exceeds maximum permitted limit of {max_size_mb} MB ({len(content)} bytes uploaded).",
        )

    if len(content) < 5:
        return False, "", "File is empty or corrupted."

    # Validate PDF magic bytes: standard PDFs begin with '%PDF-'
    # Allow finding %PDF- within the first 1024 bytes (standard for some postscript prepended PDFs)
    header = content[:1024]
    if b"%PDF-" not in header:
        return (
            False,
            "",
            "Invalid file format: file header does not contain valid PDF magic bytes (%PDF-).",
        )

    file_hash = calculate_sha256(content)
    return True, file_hash, ""
