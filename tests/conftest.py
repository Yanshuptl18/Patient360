"""Global pytest fixtures and test configuration."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Enforce testing environment before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///./test_patient360.db"

from backend.main import app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Yields a FastAPI TestClient."""
    with TestClient(app) as test_client:
        yield test_client
