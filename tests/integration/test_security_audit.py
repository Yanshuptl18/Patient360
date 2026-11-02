"""Comprehensive security audit and tenant/patient isolation test suite."""

from fastapi.testclient import TestClient


def test_unauthenticated_requests_rejected(client: TestClient) -> None:
    """Verifies that accessing protected endpoints without Bearer token returns 401 Unauthorized."""
    endpoints = [
        ("GET", "/api/v1/patients"),
        ("POST", "/api/v1/patients"),
        ("GET", "/api/v1/documents"),
        ("POST", "/api/v1/rag/query"),
        ("GET", "/api/v1/agents/patients/fake-patient/runs"),
    ]
    for method, path in endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={})
        assert res.status_code == 401, f"Expected 401 for unauthenticated {method} {path}, got {res.status_code}"


def test_patient_role_cannot_access_unauthorized_dossier(
    client: TestClient,
    reviewer_headers: dict[str, str],
    patient_headers: dict[str, str],
) -> None:
    """Verifies that a patient user cannot access another patient's dossier (IDOR defense)."""
    # Create patient record as reviewer
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-SEC-PAT-01",
            "first_name": "Sarah",
            "last_name": "Connor",
            "date_of_birth": "1965-02-28",
            "gender": "Female",
            "primary_condition": "Post-Traumatic Stress",
        },
        headers=reviewer_headers,
    )
    assert p_resp.status_code == 201
    foreign_patient_id = p_resp.json()["id"]

    # Patient attempts to read foreign dossier
    get_resp = client.get(f"/api/v1/patients/{foreign_patient_id}", headers=patient_headers)
    assert get_resp.status_code in (403, 404), f"Expected 403/404 for patient accessing foreign dossier, got {get_resp.status_code}"


def test_patient_role_cannot_delete_patient(
    client: TestClient,
    reviewer_headers: dict[str, str],
    patient_headers: dict[str, str],
) -> None:
    """Verifies that patients cannot delete patient records (GDPR cascading purge is admin only)."""
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-SEC-PAT-02",
            "first_name": "John",
            "last_name": "Connor",
            "date_of_birth": "1985-02-28",
            "gender": "Male",
        },
        headers=reviewer_headers,
    )
    assert p_resp.status_code == 201
    pid = p_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/patients/{pid}", headers=patient_headers)
    assert del_resp.status_code == 403


def test_patient_role_cannot_review_clinical_workflow(
    client: TestClient,
    reviewer_headers: dict[str, str],
    patient_headers: dict[str, str],
) -> None:
    """Verifies that patients cannot approve clinical research reports via agent workflow review endpoint."""
    # 1. Create patient
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-SEC-WORKFLOW-01",
            "first_name": "Kyle",
            "last_name": "Reese",
            "date_of_birth": "1980-05-10",
            "gender": "Male",
        },
        headers=reviewer_headers,
    )
    assert p_resp.status_code == 201
    pid = p_resp.json()["id"]

    # 2. Start research agent workflow
    start_resp = client.post(
        "/api/v1/agents/runs",
        json={
            "patient_id": pid,
            "query": "Evaluate targeted therapy for NSCLC EGFR L858R.",
        },
        headers=reviewer_headers,
    )
    assert start_resp.status_code == 201
    run_id = start_resp.json()["run_id"]

    # 3. Patient role attempts to review and approve workflow -> 403 Forbidden
    review_resp = client.post(
        f"/api/v1/agents/runs/{run_id}/review",
        json={"approved": True, "feedback": "Patient attempting unauthorized self-approval"},
        headers=patient_headers,
    )
    assert review_resp.status_code == 403
