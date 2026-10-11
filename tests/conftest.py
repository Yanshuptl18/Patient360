"""Global pytest fixtures and test configuration."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Enforce testing environment before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///./test_patient360.db"
os.environ["LLM_PROVIDER"] = "mock"

from backend.auth.service import seed_default_users
from backend.core.database import Base, SessionLocal, engine
from backend.core.security import create_access_token
from backend.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    """Creates database tables and seeds demo personas for the test session."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_users(db)
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    db_file = "./test_patient360.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Yields a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Yields a FastAPI TestClient."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_headers(db: Session) -> dict[str, str]:
    """Headers for authenticated admin user (Sarah Jenkins)."""
    from backend.auth.service import get_user_by_email

    user = get_user_by_email(db, "admin@patient360.org")
    assert user is not None
    token = create_access_token(subject=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def reviewer_headers(db: Session) -> dict[str, str]:
    """Headers for authenticated reviewer user (Dr. Evelyn Reed)."""
    from backend.auth.service import get_user_by_email

    user = get_user_by_email(db, "reviewer@patient360.org")
    assert user is not None
    token = create_access_token(subject=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def researcher_headers(db: Session) -> dict[str, str]:
    """Headers for authenticated researcher user (Dr. Marcus Vance)."""
    from backend.auth.service import get_user_by_email

    user = get_user_by_email(db, "researcher@patient360.org")
    assert user is not None
    token = create_access_token(subject=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}
