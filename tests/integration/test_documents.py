"""Integration tests for PDF upload, deduplication, and cross-patient isolation."""

import io

from fastapi.testclient import TestClient


def test_upload_valid_pdf_document(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies that a clinical reviewer can upload a PDF document for an authorized patient."""
    # 1. Create a patient
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYNTH-DOC-01",
            "first_name": "Tricia",
            "last_name": "McMillan",
            "date_of_birth": "1982-05-15",
            "gender": "female",
        },
        headers=reviewer_headers,
    )
    patient_id = p_resp.json()["id"]

    # 2. Upload valid PDF
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    files = {"file": ("Discharge_Summary.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {
        "patient_id": patient_id,
        "title": "Discharge Summary 2023",
        "doc_type": "discharge_summary",
        "doc_date": "2023-04-12",
    }

    upload_resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=reviewer_headers)
    assert upload_resp.status_code == 202
    res_data = upload_resp.json()
    assert "document_id" in res_data
    assert res_data["status"] == "pending"
    assert "file_hash_sha256" in res_data


def test_upload_non_pdf_rejected(client: TestClient, reviewer_headers: dict[str, str]) -> None:
    """Verifies that uploading a text or non-PDF file is rejected with 400 Bad Request."""
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYNTH-DOC-02",
            "first_name": "Zaphod",
            "last_name": "Beeblebrox",
            "date_of_birth": "1970-10-10",
            "gender": "male",
        },
        headers=reviewer_headers,
    )
    patient_id = p_resp.json()["id"]

    non_pdf = b"This is a text file masquerading as a PDF."
    files = {"file": ("fake.pdf", io.BytesIO(non_pdf), "application/pdf")}
    data = {"patient_id": patient_id}

    response = client.post("/api/v1/documents/upload", files=files, data=data, headers=reviewer_headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DOCUMENT"


def test_duplicate_upload_is_idempotent(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies that uploading the identical file twice for the same patient returns the same record."""
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYNTH-DOC-03",
            "first_name": "Marvin",
            "last_name": "Android",
            "date_of_birth": "1950-01-01",
            "gender": "male",
        },
        headers=reviewer_headers,
    )
    patient_id = p_resp.json()["id"]

    pdf_bytes = b"%PDF-1.4\nUnique duplicate test content\n%%EOF"
    files = {"file": ("Lab_Report.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"patient_id": patient_id, "title": "Lab Report"}

    first_resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=reviewer_headers)
    doc_id_1 = first_resp.json()["document_id"]

    # Re-upload identical file
    files_2 = {"file": ("Lab_Report_Copy.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    second_resp = client.post("/api/v1/documents/upload", files=files_2, data=data, headers=reviewer_headers)
    doc_id_2 = second_resp.json()["document_id"]

    assert doc_id_1 == doc_id_2
    assert "Duplicate document detected" in second_resp.json()["message"]


def test_cross_patient_document_access_isolation(
    client: TestClient, reviewer_headers: dict[str, str], researcher_headers: dict[str, str]
) -> None:
    """
    Verifies that User A cannot upload to or download from User B's patient documents.
    """
    # 1. Reviewer creates patient and uploads doc
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYNTH-ISO-01",
            "first_name": "Slartibartfast",
            "last_name": "Magrathea",
            "date_of_birth": "1940-08-08",
            "gender": "male",
        },
        headers=reviewer_headers,
    )
    patient_id = p_resp.json()["id"]

    pdf_bytes = b"%PDF-1.4\nConfidential patient record\n%%EOF"
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("Private.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"patient_id": patient_id},
        headers=reviewer_headers,
    )
    doc_id = upload_resp.json()["document_id"]

    # 2. Researcher attempts to upload to Reviewer's patient -> 403 Forbidden
    unauthorized_upload = client.post(
        "/api/v1/documents/upload",
        files={"file": ("Intruder.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"patient_id": patient_id},
        headers=researcher_headers,
    )
    assert unauthorized_upload.status_code == 403
    assert unauthorized_upload.json()["error"]["code"] == "FORBIDDEN"

    # 3. Researcher attempts to download Reviewer's document -> 403 Forbidden
    unauthorized_download = client.get(f"/api/v1/documents/{doc_id}/download", headers=researcher_headers)
    assert unauthorized_download.status_code == 403
    assert unauthorized_download.json()["error"]["code"] == "FORBIDDEN"

    # 4. Reviewer can download their own document -> 200 OK
    authorized_download = client.get(f"/api/v1/documents/{doc_id}/download", headers=reviewer_headers)
    assert authorized_download.status_code == 200
    assert authorized_download.content == pdf_bytes
