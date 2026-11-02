"""Integration tests for asynchronous document ingestion jobs and worker queues."""

import io

from fastapi.testclient import TestClient


def test_async_job_enqueue_and_deduplication(
    client: TestClient,
    reviewer_headers: dict[str, str],
) -> None:
    """Verifies that async ingestion enqueues jobs and deduplicates concurrent triggers."""
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-ASYNC-01",
            "first_name": "Devin",
            "last_name": "Taylor",
            "date_of_birth": "1990-03-14",
            "gender": "Male",
            "primary_condition": "Cardiomyopathy",
        },
        headers=reviewer_headers,
    )
    patient_id = p_resp.json()["id"]

    # Upload PDF
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF"
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("report.pdf", io.BytesIO(pdf_content), "application/pdf")},
        data={"title": "Cardiac MRI", "patient_id": patient_id},
        headers=reviewer_headers,
    )
    doc_id = upload_resp.json()["document_id"]

    # Enqueue async job
    enqueue_resp = client.post(f"/api/v1/documents/{doc_id}/ingest-async", headers=reviewer_headers)
    assert enqueue_resp.status_code == 202
    job_data = enqueue_resp.json()
    job_id = job_data["id"]
    assert job_data["status"] in ("queued", "processing", "completed")

    # Duplicate call while job is active returns the same job
    dup_resp = client.post(f"/api/v1/documents/{doc_id}/ingest-async", headers=reviewer_headers)
    assert dup_resp.status_code == 202
    assert dup_resp.json()["id"] == job_id

    # Retrieve job status
    status_resp = client.get(f"/api/v1/documents/jobs/{job_id}", headers=reviewer_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["document_id"] == doc_id
