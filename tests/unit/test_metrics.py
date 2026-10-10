"""Unit tests for Prometheus metrics collection, path normalization, and exposition."""

from fastapi.testclient import TestClient

from backend.core.metrics import (
    RAG_CITATIONS_TOTAL,
    RAG_QUERIES_TOTAL,
    MetricsMiddleware,
    record_rag_metrics,
)


def test_metrics_endpoint_exposition(client: TestClient) -> None:
    """Verifies GET /metrics returns HTTP 200 with standard Prometheus text format."""
    # Execute a request to generate traffic metrics
    client.get("/")

    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    content = response.text

    assert "patient360_http_requests_total" in content
    assert "patient360_http_request_duration_seconds" in content
    assert "patient360_rag_queries_total" in content
    assert "patient360_system_health_status" in content


def test_metrics_middleware_path_normalization() -> None:
    """Verifies path normalization prevents label cardinality explosion from UUIDs."""
    test_cases = [
        ("/api/v1/patients/123e4567-e89b-12d3-a456-426614174000", "/api/v1/patients/{id}"),
        ("/api/v1/patients/pat-10001", "/api/v1/patients/{id}"),
        ("/api/v1/documents/doc-9999", "/api/v1/documents/{id}"),
        ("/api/v1/patients/12345/permissions", "/api/v1/patients/{id}/permissions"),
        ("/health", "/health"),
        ("/api/v1/rag/query", "/api/v1/rag/query"),
    ]

    for raw_path, expected in test_cases:
        normalized = MetricsMiddleware._normalize_path(raw_path)
        assert normalized == expected, f"Failed for {raw_path}: expected {expected}, got {normalized}"


def test_record_rag_metrics_collector() -> None:
    """Verifies that record_rag_metrics increments Prometheus counters."""
    initial_supported = RAG_CITATIONS_TOTAL.labels(status="supported")._value.get()
    initial_unsupported = RAG_CITATIONS_TOTAL.labels(status="unsupported")._value.get()
    initial_queries = RAG_QUERIES_TOTAL.labels(is_abstention="false", is_emergency="false")._value.get()

    record_rag_metrics(
        is_abstention=False,
        is_emergency=False,
        latency_seconds=0.15,
        supported_citations=2,
        unsupported_citations=1,
    )

    new_supported = RAG_CITATIONS_TOTAL.labels(status="supported")._value.get()
    new_unsupported = RAG_CITATIONS_TOTAL.labels(status="unsupported")._value.get()
    new_queries = RAG_QUERIES_TOTAL.labels(is_abstention="false", is_emergency="false")._value.get()

    assert new_supported == initial_supported + 2
    assert new_unsupported == initial_unsupported + 1
    assert new_queries == initial_queries + 1
