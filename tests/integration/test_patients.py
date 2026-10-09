"""Integration tests for patient dossier CRUD and server-side isolation."""

from fastapi.testclient import TestClient


def test_create_patient_reviewer(client: TestClient, reviewer_headers: dict[str, str]) -> None:
    """Verifies that a clinical reviewer can register a synthetic patient dossier."""
    payload = {
        "mrn_synthetic": "SYNTH-10001",
        "first_name": "Eleanor",
        "last_name": "Vance",
        "date_of_birth": "1964-08-14",
        "gender": "female",
        "primary_condition": "Cardio-Oncology / Heart Failure",
    }
    response = client.post("/api/v1/patients", json=payload, headers=reviewer_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["mrn_synthetic"] == "SYNTH-10001"
    assert data["first_name"] == "Eleanor"
    assert "id" in data


def test_duplicate_mrn_rejected(client: TestClient, reviewer_headers: dict[str, str]) -> None:
    """Verifies duplicate synthetic MRN is rejected with 409 Conflict."""
    payload = {
        "mrn_synthetic": "SYNTH-10001",
        "first_name": "Duplicate",
        "last_name": "Patient",
        "date_of_birth": "1980-01-01",
        "gender": "male",
    }
    response = client.post("/api/v1/patients", json=payload, headers=reviewer_headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PATIENT_ALREADY_EXISTS"


def test_patient_isolation_enforcement(
    client: TestClient, reviewer_headers: dict[str, str], researcher_headers: dict[str, str]
) -> None:
    """
    Critical isolation test:
    Reviewer creates Patient A.
    Researcher queries /patients -> Patient A must NOT be listed.
    Researcher directly queries /patients/{id} -> Must return 403 Forbidden.
    """
    # 1. Reviewer creates patient
    payload = {
        "mrn_synthetic": "SYNTH-SECRET-99",
        "first_name": "Arthur",
        "last_name": "Dent",
        "date_of_birth": "1978-03-11",
        "gender": "male",
        "primary_condition": "Hypertension",
    }
    create_resp = client.post("/api/v1/patients", json=payload, headers=reviewer_headers)
    assert create_resp.status_code == 201
    patient_id = create_resp.json()["id"]

    # 2. Reviewer can see patient in list
    rev_list = client.get("/api/v1/patients", headers=reviewer_headers).json()
    assert any(p["id"] == patient_id for p in rev_list)

    # 3. Researcher does NOT see patient in list
    res_list = client.get("/api/v1/patients", headers=researcher_headers).json()
    assert not any(p["id"] == patient_id for p in res_list)

    # 4. Researcher direct access returns 403 Forbidden
    direct_resp = client.get(f"/api/v1/patients/{patient_id}", headers=researcher_headers)
    assert direct_resp.status_code == 403
    assert direct_resp.json()["error"]["code"] == "FORBIDDEN"


def test_admin_platform_wide_patient_visibility(
    client: TestClient, reviewer_headers: dict[str, str], admin_headers: dict[str, str]
) -> None:
    """Verifies that Administrator has global visibility across all patient dossiers."""
    payload = {
        "mrn_synthetic": "SYNTH-ADMIN-TEST",
        "first_name": "Ford",
        "last_name": "Prefect",
        "date_of_birth": "1975-02-20",
        "gender": "male",
    }
    create_resp = client.post("/api/v1/patients", json=payload, headers=reviewer_headers)
    patient_id = create_resp.json()["id"]

    # Admin accesses patient directly
    admin_resp = client.get(f"/api/v1/patients/{patient_id}", headers=admin_headers)
    assert admin_resp.status_code == 200
    assert admin_resp.json()["mrn_synthetic"] == "SYNTH-ADMIN-TEST"
