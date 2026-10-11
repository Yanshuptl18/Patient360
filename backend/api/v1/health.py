"""System health and diagnostic probes."""

import time
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.config import settings
from backend.core.database import check_database_connection

router = APIRouter()

APP_START_TIME = time.time()


class ComponentHealth(BaseModel):
    status: str
    latency_ms: int
    message: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str
    uptime_seconds: int
    timestamp: str
    components: dict[str, ComponentHealth]


def check_qdrant_health() -> tuple[bool, int, str]:
    """Checks Qdrant REST API liveness or active vector store instance."""
    start = time.perf_counter()

    # Fast path: Check active vector store singleton first if embedded
    try:
        from backend.vector.store import get_vector_store

        store = get_vector_store()
        if getattr(store, "is_embedded", False):
            stats = store.get_collection_stats()
            latency_ms = max(1, int((time.perf_counter() - start) * 1000))
            return True, latency_ms, f"Qdrant vector engine ready (Embedded, {stats.get('vectors_count', 0)} vectors)"
    except Exception:
        pass

    url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/readyz"
    try:
        with httpx.Client(timeout=0.5) as client:
            resp = client.get(url)
            latency_ms = int((time.perf_counter() - start) * 1000)
            if resp.status_code == 200:
                return True, latency_ms, "Qdrant vector engine ready (Standalone daemon)"
    except Exception:
        pass

    # Check active vector store status
    try:
        from backend.vector.store import get_vector_store

        store = get_vector_store()
        stats = store.get_collection_stats()
        latency_ms = int((time.perf_counter() - start) * 1000)
        if stats.get("status") == "UP":
            mode = "Embedded" if stats.get("is_embedded") else "Standalone"
            return True, latency_ms, f"Qdrant vector engine ready ({mode}, {stats.get('vectors_count', 0)} vectors)"
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return False, latency_ms, f"Qdrant vector engine error: {str(exc)[:80]}"

    latency_ms = int((time.perf_counter() - start) * 1000)
    return False, latency_ms, "Qdrant unreachable"


def check_storage_health() -> tuple[bool, int, str]:
    """Checks that the document storage directory is accessible and writeable."""
    start = time.perf_counter()
    try:
        storage_dir = settings.storage_path
        test_file = storage_dir / ".probe_check.tmp"
        test_file.write_text("probe")
        test_file.unlink()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return True, latency_ms, f"Storage directory writeable at {storage_dir}"
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return False, latency_ms, f"Storage write check failed: {str(exc)[:80]}"


_last_llm_check_time = 0.0
_last_llm_check_result: tuple[bool, int, str] | None = None


def check_llm_health() -> tuple[bool, int, str]:
    """Checks configured LLM provider connectivity (Gemini, Ollama, or Mock), cached for 30s."""
    global _last_llm_check_time, _last_llm_check_result
    now = time.time()
    if _last_llm_check_result is not None and (now - _last_llm_check_time) < 30.0:
        return _last_llm_check_result

    try:
        from backend.rag.llm import get_llm_provider

        provider = get_llm_provider()
        res = provider.check_health()
        _last_llm_check_result = res
        _last_llm_check_time = now
        return res
    except Exception as exc:
        return False, 0, f"LLM provider error: {exc}"


@router.get("", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """
    Comprehensive system health probe assessing:
    - PostgreSQL connection
    - Qdrant vector database liveness
    - Local document storage filesystem writeability
    - Configured LLM provider connectivity
    """
    db_ok, db_lat, db_msg = check_database_connection()
    qd_ok, qd_lat, qd_msg = check_qdrant_health()
    st_ok, st_lat, st_msg = check_storage_health()
    llm_ok, llm_lat, llm_msg = check_llm_health()

    components = {
        "database": ComponentHealth(
            status="UP" if db_ok else "DOWN",
            latency_ms=db_lat,
            message=db_msg,
        ),
        "vector_store": ComponentHealth(
            status="UP" if qd_ok else "DOWN",
            latency_ms=qd_lat,
            message=qd_msg,
        ),
        "storage": ComponentHealth(
            status="UP" if st_ok else "DOWN",
            latency_ms=st_lat,
            message=st_msg,
        ),
        "llm_provider": ComponentHealth(
            status="UP" if llm_ok else "DOWN",
            latency_ms=llm_lat,
            message=llm_msg,
        ),
    }

    core_healthy = db_ok and qd_ok and st_ok
    if core_healthy and llm_ok:
        overall_status = "HEALTHY"
    elif db_ok or qd_ok or st_ok:
        overall_status = "DEGRADED"
    else:
        overall_status = "UNHEALTHY"

    return HealthResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        uptime_seconds=int(time.time() - APP_START_TIME),
        timestamp=datetime.now(UTC).isoformat(),
        components=components,
    )
