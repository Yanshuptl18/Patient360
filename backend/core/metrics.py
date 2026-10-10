"""Prometheus observability collectors and metrics exporter for Patient360."""

import time
from typing import ClassVar

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# 1. HTTP Traffic & Latency Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "patient360_http_requests_total",
    "Total HTTP requests received by the API service",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "patient360_http_request_duration_seconds",
    "HTTP request latency distribution in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# 2. RAG Pipeline Performance & Clinical Quality Metrics
RAG_QUERIES_TOTAL = Counter(
    "patient360_rag_queries_total",
    "Total evidence-grounded clinical RAG queries executed",
    ["is_abstention", "is_emergency"],
)

RAG_QUERY_DURATION_SECONDS = Histogram(
    "patient360_rag_query_duration_seconds",
    "End-to-end RAG query execution duration in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
)

RAG_CITATIONS_TOTAL = Counter(
    "patient360_rag_citations_total",
    "Extracted citation attributions by verification status",
    ["status"],
)

# 3. Document Ingestion Pipeline Metrics
DOCUMENT_INGESTION_TOTAL = Counter(
    "patient360_document_ingestion_total",
    "Total documents processed through ingestion pipeline",
    ["doc_type", "status"],
)

# 4. System & Health Gauge
SYSTEM_HEALTH_GAUGE = Gauge(
    "patient360_system_health_status",
    "Current overall system operational health score (1=Healthy, 0=Degraded/Down)",
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware recording Prometheus metrics for incoming HTTP requests.
    Normalizes variable path parameters to prevent label cardinality explosion.
    """

    EXCLUDED_PATHS: ClassVar[set[str]] = {"/metrics", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Normalize common parameterized IDs (e.g. UUIDs or alphanumeric IDs)
        normalized_path = self._normalize_path(path)
        method = request.method
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            return response
        except Exception:
            status_code = "500"
            raise
        finally:
            duration = max(0.0001, time.perf_counter() - start_time)
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=normalized_path,
                status=status_code,
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=normalized_path,
            ).observe(duration)

    @staticmethod
    def _normalize_path(path: str) -> str:
        parts = path.strip("/").split("/")
        normalized = []
        for part in parts:
            # Check for UUID or numeric ID format
            if len(part) in (36, 32) and ("-" in part or part.isalnum()):
                normalized.append("{id}")
            elif part.isdigit():
                normalized.append("{id}")
            elif part.startswith("pat-") or part.startswith("doc-"):
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/" + "/".join(normalized) if normalized else "/"


def record_rag_metrics(
    is_abstention: bool,
    is_emergency: bool,
    latency_seconds: float,
    supported_citations: int = 0,
    unsupported_citations: int = 0,
) -> None:
    """Helper for incrementing RAG metrics in business logic."""
    RAG_QUERIES_TOTAL.labels(
        is_abstention=str(is_abstention).lower(),
        is_emergency=str(is_emergency).lower(),
    ).inc()
    RAG_QUERY_DURATION_SECONDS.observe(latency_seconds)

    if supported_citations > 0:
        RAG_CITATIONS_TOTAL.labels(status="supported").inc(supported_citations)
    if unsupported_citations > 0:
        RAG_CITATIONS_TOTAL.labels(status="unsupported").inc(unsupported_citations)


def generate_prometheus_response() -> Response:
    """Returns formatted Prometheus exposition text format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
