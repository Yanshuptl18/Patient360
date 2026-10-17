"""SQLAlchemy engine, session management, and connectivity probes."""

import logging
import tempfile
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Base Declarative Model
Base = declarative_base()


def _create_robust_engine():
    """Initializes a resilient SQLAlchemy engine with directory validation and fallbacks."""
    db_url = settings.DATABASE_URL
    engine_kwargs: dict[str, Any] = {"echo": False}

    if db_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if "///" in db_url and not db_url.endswith(":memory:"):
            db_path_str = db_url.split("///")[-1]
            try:
                p = Path(db_path_str).resolve()
                p.parent.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                logger.warning(f"Could not create database directory for {db_path_str}: {exc}")
    else:
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10

    try:
        eng = create_engine(db_url, **engine_kwargs)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return eng
    except Exception as err:
        logger.warning(
            f"Configured database ({db_url}) initialization failed: {err}. "
            "Engaging writeable local SQLite fallback."
        )
        fallback_path = Path(tempfile.gettempdir()) / "patient360_runtime.db"
        try:
            fallback_url = f"sqlite:///{fallback_path.as_posix()}"
            eng = create_engine(fallback_url, connect_args={"check_same_thread": False})
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Connected to fallback database at {fallback_url}")
            return eng
        except Exception as fallback_err:
            logger.error(f"Fallback SQLite failed ({fallback_err}), using in-memory SQLite.")
            return create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})


engine = _create_robust_engine()
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
        latency_ms = max(1, int((time.perf_counter() - start) * 1000))
        dialect_name = engine.dialect.name
        return True, latency_ms, f"{dialect_name.capitalize()} database connected and operational"
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.warning(f"Database connection check failed: {exc}")
        return False, latency_ms, f"Connection failed: {str(exc)[:100]}"
