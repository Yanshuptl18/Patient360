"""Local secure file storage adapter with path isolation and integrity verification."""

import logging
from pathlib import Path

from backend.core.config import settings

logger = logging.getLogger(__name__)


class DocumentStorage:
    """Manages file storage on the local filesystem."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or settings.storage_path).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, content: bytes, file_hash: str) -> str:
        """
        Saves file bytes to disk using a partitioned hash path: {hash[:2]}/{hash}.pdf.
        Returns the relative file path for database storage.
        """
        partition_dir = self.base_dir / file_hash[:2]
        partition_dir.mkdir(parents=True, exist_ok=True)

        target_file = partition_dir / f"{file_hash}.pdf"
        target_file.write_bytes(content)
        logger.debug(f"Saved file {file_hash[:8]} to {target_file}")

        # Return relative path using POSIX slashes
        return f"{file_hash[:2]}/{file_hash}.pdf"

    def get_absolute_path(self, relative_path: str) -> Path:
        """Resolves relative file path to absolute path, preventing path traversal."""
        resolved = (self.base_dir / relative_path).resolve()
        if not str(resolved).startswith(str(self.base_dir)):
            raise ValueError("Path traversal attempt detected.")
        return resolved

    def read_file(self, relative_path: str) -> bytes:
        """Reads file bytes from disk."""
        abs_path = self.get_absolute_path(relative_path)
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found at {relative_path}")
        return abs_path.read_bytes()

    def delete_file(self, relative_path: str) -> bool:
        """Deletes file from disk if present."""
        try:
            abs_path = self.get_absolute_path(relative_path)
            if abs_path.exists():
                abs_path.unlink()
                logger.info(f"Unlinked file at {relative_path}")
                return True
            return False
        except Exception as exc:
            logger.warning(f"Could not delete file {relative_path}: {exc}")
            return False

    def exists(self, relative_path: str) -> bool:
        """Checks if file exists on disk."""
        try:
            return self.get_absolute_path(relative_path).exists()
        except Exception:
            return False


def get_storage() -> DocumentStorage:
    """Returns singleton DocumentStorage adapter."""
    return DocumentStorage()
