"""Integration tests for root and health probe endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    """Verifies root endpoint returns project metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "Patient360" in data["project"]
    assert "health_url" in data
    assert "notice" in data


def test_basic_health_endpoint(client: TestClient) -> None:
    """Verifies basic /health liveness probe."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert "version" in data


def test_detailed_health_endpoint(client: TestClient) -> None:
    """Verifies /api/v1/health returns structured component health."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["HEALTHY", "DEGRADED", "UNHEALTHY"]
    assert "components" in data
    assert "database" in data["components"]
    assert "vector_store" in data["components"]
    assert "storage" in data["components"]
    assert "llm_provider" in data["components"]
    assert data["components"]["storage"]["status"] == "UP"
    assert data["components"]["llm_provider"]["status"] in ["UP", "DOWN"]
