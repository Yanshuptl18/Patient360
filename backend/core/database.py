"""SQLAlchemy engine, session management, and connectivity probes."""

import logging
import time
from typing import Any, Generator
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

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

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
