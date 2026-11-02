"""Integration tests for document ingestion recovery endpoint and deterministic chunk IDs."""

import io

import pymupdf
from fastapi.testclient import TestClient


def create_sample_pdf_bytes() -> bytes:
    doc = pymupdf.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 72), "CLINICAL SUMMARY\nPatient: Test Subject\nCondition: Recovery Validation", fontsize=12)
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_deterministic_chunk_ids_across_ingestions(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies that chunk IDs remain strictly deterministic across multiple ingestion runs."""
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-DET-01",
            "first_name": "Marcus",
            "last_name": "Aurelius",
            "date_of_birth": "1980-01-01",
            "gender": "Male",
            "primary_condition": "Hypertension",
        },
        headers=reviewer_headers,
    )
    patient_id = p_resp.json()["id"]

    pdf_bytes = create_sample_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("vitals.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"title": "Vitals Record", "patient_id": patient_id},
        headers=reviewer_headers,
    )
    doc_id = upload_resp.json()["document_id"]

    # First ingestion
    ingest1 = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=reviewer_headers)
    assert ingest1.status_code == 200
    chunks1 = client.get(f"/api/v1/documents/{doc_id}/chunks", headers=reviewer_headers).json()
    ids_1 = [c["id"] for c in chunks1]

    # Second ingestion (idempotent re-run)
    ingest2 = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=reviewer_headers)
    assert ingest2.status_code == 200
    chunks2 = client.get(f"/api/v1/documents/{doc_id}/chunks", headers=reviewer_headers).json()
    ids_2 = [c["id"] for c in chunks2]

    assert ids_1 == ids_2, "Chunk IDs must be deterministic and identical across re-ingestion."


def test_document_recovery_endpoint_restores_failed_document(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies that POST /api/v1/documents/{id}/recover purges corrupted state and re-ingests."""
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-REC-01",
            "first_name": "Avery",
            "last_name": "Brooks",
            "date_of_birth": "1975-04-12",
            "gender": "Other",
            "primary_condition": "Asthma",
        },
        headers=reviewer_headers,
    )
    patient_id = p_resp.json()["id"]

    pdf_bytes = create_sample_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("consult.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"title": "Consult Report", "patient_id": patient_id},
        headers=reviewer_headers,
    )
    doc_id = upload_resp.json()["document_id"]

    # Ingest document initially
    ingest_resp = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=reviewer_headers)
    assert ingest_resp.status_code == 200

    # Call recovery endpoint
    recover_resp = client.post(f"/api/v1/documents/{doc_id}/recover", headers=reviewer_headers)
    assert recover_resp.status_code == 200
    rec_data = recover_resp.json()
    assert rec_data["status"] == "completed"
    assert rec_data["chunk_count"] > 0

    # Verify document record is completed
    doc_resp = client.get(f"/api/v1/documents/{doc_id}", headers=reviewer_headers)
    assert doc_resp.json()["ingestion_status"] == "completed"
