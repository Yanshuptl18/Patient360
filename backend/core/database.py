"""SQLAlchemy engine, session management, and connectivity probes."""

import logging
import time
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Base Declarative Model
Base = declarative_base()

# Configure SQLAlchemy Engine
# For SQLite, check_same_thread is False; for Postgres, pool settings apply
engine_kwargs: dict[str, Any] = {"echo": False}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10

try:
    engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as err:
    if not settings.DATABASE_URL.startswith("sqlite"):
        logger.warning(
            f"Configured primary database unreachable ({err}). "
            "Falling back to local SQLite database at './patient360_dev.db'."
        )
        engine = create_engine("sqlite:///./patient360_dev.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding transactional database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> tuple[bool, int, str]:
    """
    Checks database health via a lightweight SELECT 1 query.
    Returns: (is_healthy, latency_ms, status_message)
    """
    start = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        latency_ms = int((time.perf_counter() - start) * 1000)
        return True, latency_ms, "PostgreSQL connected and responsive"
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.warning(f"Database connection check failed: {exc}")
        return False, latency_ms, f"Connection failed: {str(exc)[:100]}"
