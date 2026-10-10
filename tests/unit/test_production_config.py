"""Unit tests verifying production deployment assets, Dockerfiles, and Nginx reverse proxy configuration."""

from pathlib import Path


def test_backend_dockerfile_structure() -> None:
    """Verifies backend Dockerfile enforces multi-stage build, unprivileged user, and healthcheck."""
    df_path = Path("deployment/docker/backend.Dockerfile")
    assert df_path.exists(), "backend.Dockerfile missing"
    content = df_path.read_text(encoding="utf-8")

    assert "AS builder" in content
    assert "AS runner" in content
    assert "useradd" in content
    assert "USER appuser" in content
    assert "HEALTHCHECK" in content
    assert "uvicorn" in content


def test_frontend_dockerfile_structure() -> None:
    """Verifies frontend Dockerfile compiles via Node.js and serves via hardened Nginx."""
    df_path = Path("deployment/docker/frontend.Dockerfile")
    assert df_path.exists(), "frontend.Dockerfile missing"
    content = df_path.read_text(encoding="utf-8")

    assert "AS builder" in content
    assert "node:20-alpine" in content
    assert "nginx:1.27-alpine" in content
    assert "npm run build" in content
    assert "HEALTHCHECK" in content


def test_nginx_conf_security_and_proxy_rules() -> None:
    """Verifies Nginx configuration includes security headers, gzip, and proxy directives."""
    conf_path = Path("deployment/nginx/nginx.conf")
    assert conf_path.exists(), "nginx.conf missing"
    content = conf_path.read_text(encoding="utf-8")

    assert "gzip on;" in content
    assert "X-Frame-Options \"DENY\"" in content
    assert "X-Content-Type-Options \"nosniff\"" in content
    assert "proxy_pass http://backend_upstream;" in content
    assert "location /metrics" in content
    assert "try_files $uri $uri/ /index.html;" in content


def test_docker_compose_prod_specification() -> None:
    """Verifies production docker-compose defines resource constraints and isolated services."""
    compose_path = Path("deployment/docker-compose.prod.yml")
    assert compose_path.exists(), "docker-compose.prod.yml missing"
    content = compose_path.read_text(encoding="utf-8")

    # Check services
    assert "postgres:" in content
    assert "qdrant:" in content
    assert "backend:" in content
    assert "frontend:" in content

    # Check resource limits
    assert "memory: 512M" in content
    assert "memory: 256M" in content

    # Check restart policy
    assert "restart: unless-stopped" in content


def test_ci_workflow_specification() -> None:
    """Verifies GitHub Actions CI workflow defines all required verification jobs."""
    ci_path = Path(".github/workflows/ci.yml")
    assert ci_path.exists(), "ci.yml missing"
    content = ci_path.read_text(encoding="utf-8")

    assert "backend-lint-and-typecheck:" in content
    assert "backend-test-suite:" in content
    assert "frontend-build:" in content
    assert "deployment-config-validation:" in content
    assert "ruff check ." in content
    assert "mypy backend" in content
    assert "pytest" in content
    assert "npm run build" in content
