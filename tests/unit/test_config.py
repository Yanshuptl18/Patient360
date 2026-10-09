"""Unit tests for configuration and settings."""

from backend.core.config import Settings


def test_settings_default_values() -> None:
    """Verifies that Settings loads expected defaults."""
    s = Settings()
    assert s.PROJECT_NAME == "Patient360 Healthcare Intelligence Platform"
    assert s.VERSION == "0.1.0"
    assert s.API_V1_STR == "/api/v1"
    assert s.MAX_UPLOAD_SIZE_MB == 25
    assert s.MAX_CONTEXT_TOKENS == 2000
    assert s.EMBEDDING_DIMENSIONS == 384


def test_settings_storage_path_creation() -> None:
    """Verifies that storage_path property creates and resolves directory."""
    s = Settings(STORAGE_LOCAL_PATH="./storage/test_docs")
    path = s.storage_path
    assert path.exists()
    assert path.is_dir()
    # Cleanup test dir
    path.rmdir()
