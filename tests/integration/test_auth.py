"""Integration tests for authentication endpoints and RBAC route enforcement."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.audit import AuditLog


def test_login_success(client: TestClient) -> None:
    """Verifies that valid credentials return access and refresh tokens."""
    payload = {
        "email": "reviewer@patient360.org",
        "password": "Patient360Secure!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "reviewer@patient360.org"
    assert data["user"]["role"] == "reviewer"


def test_login_invalid_password(client: TestClient) -> None:
    """Verifies that invalid password returns 401 Unauthorized."""
    payload = {
        "email": "reviewer@patient360.org",
        "password": "WrongPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_login_audit_trail_created(client: TestClient, db: Session) -> None:
    """Verifies that login attempts generate append-only audit log records."""
    initial_count = db.query(AuditLog).count()
    payload = {
        "email": "admin@patient360.org",
        "password": "Patient360Secure!",
    }
    client.post("/api/v1/auth/login", json=payload)
    new_count = db.query(AuditLog).count()
    assert new_count > initial_count

    latest = db.query(AuditLog).order_by(AuditLog.created_at.desc()).first()
    assert latest is not None
    assert latest.action in ["LOGIN_SUCCESS", "LOGIN_ATTEMPT"]


def test_get_current_user_profile(client: TestClient, reviewer_headers: dict[str, str]) -> None:
    """Verifies /me returns authenticated user demographic profile."""
    response = client.get("/api/v1/auth/me", headers=reviewer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "reviewer@patient360.org"
    assert data["role"] == "reviewer"
    assert data["full_name"] == "Dr. Evelyn Reed"


def test_get_current_user_unauthorized(client: TestClient) -> None:
    """Verifies /me without authorization header returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_token_refresh(client: TestClient) -> None:
    """Verifies that a valid refresh token issues a new access token."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "researcher@patient360.org", "password": "Patient360Secure!"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "researcher@patient360.org"


def test_admin_list_users_authorized(client: TestClient, admin_headers: dict[str, str]) -> None:
    """Verifies admin role can access /users endpoint."""
    response = client.get("/api/v1/auth/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4  # Seeded personas


def test_admin_list_users_forbidden_for_reviewer(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies that reviewer role is rejected with 403 Forbidden on admin endpoint."""
    response = client.get("/api/v1/auth/users", headers=reviewer_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "FORBIDDEN"


def test_admin_create_user(client: TestClient, admin_headers: dict[str, str]) -> None:
    """Verifies admin can provision a new user."""
    new_user_data = {
        "email": "nurse.clara@patient360.org",
        "full_name": "Nurse Clara Oswald",
        "role": "reviewer",
        "password": "SecurePassword123!",
    }
    response = client.post("/api/v1/auth/users", json=new_user_data, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "nurse.clara@patient360.org"
    assert data["full_name"] == "Nurse Clara Oswald"
    assert data["role"] == "reviewer"
