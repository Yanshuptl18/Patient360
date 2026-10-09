"""Integration tests for document ingestion, parsing, chunk generation, and isolation."""

import io

import pymupdf
from fastapi.testclient import TestClient


def create_multipage_pdf_bytes() -> bytes:
    """Creates a real 2-page clinical PDF in memory."""
    doc = pymupdf.open()
    # Page 1
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 72),
        "CLINICAL CONSULTATION REPORT\nPatient: Eleanor Vance\nChief Complaint: Severe cough.\n"
        "Impression: Suspected NSCLC. Schedule CT scan and molecular NGS panel.",
        fontsize=11,
    )
    # Page 2
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(
        (50, 72),
        "GENOMIC BIOMARKER PROFILE\nFindings: EGFR L858R mutation positive in exon 21.\n"
        "Plan: Targeted tyrosine kinase inhibitor therapy recommended.",
        fontsize=11,
    )
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_end_to_end_document_ingestion(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies complete flow: upload PDF -> trigger ingestion -> verify chunks and page provenance."""
    headers = reviewer_headers

    # 1. Create Patient
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-INGEST-01",
            "first_name": "Eleanor",
            "last_name": "Vance",
            "date_of_birth": "1978-06-15",
            "gender": "Female",
            "primary_condition": "NSCLC",
        },
        headers=headers,
    )
    assert p_resp.status_code == 201
    patient_id = p_resp.json()["id"]

    # 2. Upload 2-page PDF
    pdf_bytes = create_multipage_pdf_bytes()
    files = {"file": ("oncology_consult.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {
        "title": "Oncology Consultation & NGS",
        "doc_type": "patient_record",
        "doc_date": "2024-03-20",
        "patient_id": patient_id,
    }
    upload_resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert upload_resp.status_code == 202
    doc_id = upload_resp.json()["document_id"]
    assert upload_resp.json()["status"] == "pending"

    # 3. Trigger Ingestion
    ingest_resp = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)
    assert ingest_resp.status_code == 200
    ingest_data = ingest_resp.json()
    assert ingest_data["status"] == "completed"
    assert ingest_data["pages_processed"] == 2
    assert ingest_data["chunk_count"] >= 2
    assert ingest_data["total_tokens"] > 0

    # 4. Fetch Chunks and verify physical page provenance
    chunks_resp = client.get(f"/api/v1/documents/{doc_id}/chunks", headers=headers)
    assert chunks_resp.status_code == 200
    chunks = chunks_resp.json()
    assert len(chunks) == ingest_data["chunk_count"]

    # Verify both page 1 and page 2 are represented
    page_numbers = {c["page_number"] for c in chunks}
    assert 1 in page_numbers
    assert 2 in page_numbers

    # Verify context header
    first_chunk = chunks[0]
    assert "[Document: Oncology Consultation & NGS | Page: 1 | Date: 2024-03-20]" in first_chunk["content"]
    assert first_chunk["token_count"] > 0

    # 5. Idempotent re-ingestion
    reingest_resp = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)
    assert reingest_resp.status_code == 200
    assert reingest_resp.json()["chunk_count"] == ingest_data["chunk_count"]


def test_ingestion_cross_patient_isolation(
    client: TestClient,
    reviewer_headers: dict[str, str],
    researcher_headers: dict[str, str],
) -> None:
    """Verifies that unauthorized users cannot trigger ingestion or read chunks."""
    # Reviewer creates a patient and uploads a document
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-INGEST-SEC-01",
            "first_name": "Private",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
        },
        headers=reviewer_headers,
    )
    patient_id = p_resp.json()["id"]

    pdf_bytes = create_multipage_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("private.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"title": "Private Note", "patient_id": patient_id},
        headers=reviewer_headers,
    )
    assert upload_resp.status_code == 202
    doc_id = upload_resp.json()["document_id"]

    # Ingest document as reviewer
    client.post(
        f"/api/v1/documents/{doc_id}/ingest",
        headers=reviewer_headers,
    )

    # Researcher attempts to access chunks (must be 403 Forbidden)
    chunks_forbidden = client.get(
        f"/api/v1/documents/{doc_id}/chunks",
        headers=researcher_headers,
    )
    assert chunks_forbidden.status_code == 403

    # Researcher attempts to trigger ingestion (must be 403 Forbidden)
    ingest_forbidden = client.post(
        f"/api/v1/documents/{doc_id}/ingest",
        headers=researcher_headers,
    )
    assert ingest_forbidden.status_code == 403
