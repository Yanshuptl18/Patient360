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
    url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/readyz"
    try:
        with httpx.Client(timeout=1.0) as client:
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


@router.get("", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """
    Comprehensive system health probe assessing:
    - PostgreSQL connection
    - Qdrant vector database liveness
    - Local document storage filesystem writeability
    """
    db_ok, db_lat, db_msg = check_database_connection()
    qd_ok, qd_lat, qd_msg = check_qdrant_health()
    st_ok, st_lat, st_msg = check_storage_health()

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
    }

    if db_ok and qd_ok and st_ok:
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
