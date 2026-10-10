"""Integration tests for hybrid retrieval (Dense + Sparse BM25 + RRF) and API endpoints."""

import io

import pymupdf
from fastapi.testclient import TestClient


def create_hybrid_sample_pdf() -> bytes:
    """Creates a sample PDF with specific clinical terms and exact numeric markers."""
    doc = pymupdf.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 72),
        "CARDIOLOGY CLINIC PROGRESS NOTE\nPatient: Harold Finch (MRN: SYN-HYBRID-01)\n"
        "Chief Complaint: Dyspnea on minimal exertion and peripheral edema.\n"
        "Labs: Serum NT-proBNP markedly elevated at 5280 pg/mL.\n"
        "Assessment: Decompensated congestive heart failure with preserved ejection fraction.",
        fontsize=11,
    )
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(
        (50, 72),
        "RENAL PROFILE & ELECTROLYTES\n"
        "Serum Creatinine: 1.8 mg/dL (Baseline 1.1 mg/dL).\n"
        "eGFR: 38 mL/min/1.73m2 consistent with Stage 3b CKD.\n"
        "Plan: Adjust diuretic regimen and monitor electrolytes in 48 hours.",
        fontsize=11,
    )
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_hybrid_search_api_endpoint(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies that POST /api/v1/vector/hybrid-search returns RRF-merged candidates."""
    headers = reviewer_headers

    # 1. Register patient
    patient_resp = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "mrn_synthetic": "SYN-HYB-001",
            "first_name": "Harold",
            "last_name": "Finch",
            "date_of_birth": "1962-09-15",
            "gender": "male",
            "primary_condition": "Heart Failure",
        },
    )
    assert patient_resp.status_code == 201
    patient_id = patient_resp.json()["id"]

    # 2. Upload PDF
    pdf_content = create_hybrid_sample_pdf()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "title": "Cardiorenal_Evaluation.pdf",
            "doc_type": "patient_record",
            "doc_date": "2024-04-10",
        },
        files={"file": ("Cardiorenal_Evaluation.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert upload_resp.status_code == 202
    doc_id = upload_resp.json()["document_id"]

    # 3. Ingest document
    ingest_resp = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)
    assert ingest_resp.status_code == 200

    # 4. Perform hybrid search for exact acronym
    search_resp = client.post(
        "/api/v1/vector/hybrid-search",
        headers=headers,
        json={
            "query": "NT-proBNP biomarker",
            "patient_id": patient_id,
            "top_k": 5,
            "rrf_k": 60,
        },
    )
    assert search_resp.status_code == 200
    results = search_resp.json()

    assert len(results) >= 1
    top_hit = results[0]
    assert "NT-proBNP" in top_hit["content"]
    assert top_hit["rrf_score"] > 0.0
    assert top_hit["sparse_rank"] is not None
    assert top_hit["page_number"] == 1


def test_hybrid_search_cross_patient_rejection(
    client: TestClient, admin_headers: dict[str, str], reviewer_headers: dict[str, str]
) -> None:
    """Verifies that non-permitted clinicians cannot query unauthorized dossiers via hybrid search."""
    # Admin creates private dossier
    patient_resp = client.post(
        "/api/v1/patients",
        headers=admin_headers,
        json={
            "mrn_synthetic": "SYN-HYB-002",
            "first_name": "Root",
            "last_name": "Groves",
            "date_of_birth": "1980-05-12",
            "gender": "female",
        },
    )
    assert patient_resp.status_code == 201
    patient_id = patient_resp.json()["id"]

    # Reviewer queries without access
    resp = client.post(
        "/api/v1/vector/hybrid-search",
        headers=reviewer_headers,
        json={
            "query": "Heart failure",
            "patient_id": patient_id,
            "top_k": 5,
        },
    )
    assert resp.status_code == 403


def test_rag_query_with_hybrid_metadata(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies that RAG query executes hybrid search and reports dense & sparse telemetry."""
    headers = reviewer_headers

    patient_resp = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "mrn_synthetic": "SYN-HYB-003",
            "first_name": "John",
            "last_name": "Reese",
            "date_of_birth": "1975-03-20",
            "gender": "male",
        },
    )
    assert patient_resp.status_code == 201
    patient_id = patient_resp.json()["id"]

    pdf_content = create_hybrid_sample_pdf()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "title": "Renal_Progress.pdf",
            "doc_type": "lab_report",
            "doc_date": "2024-04-12",
        },
        files={"file": ("Renal_Progress.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert upload_resp.status_code == 202
    doc_id = upload_resp.json()["document_id"]
    client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)

    # Query for eGFR and renal impairment
    rag_resp = client.post(
        "/api/v1/rag/query",
        headers=headers,
        json={
            "query": "What is the patient's eGFR level?",
            "patient_id": patient_id,
            "top_k": 5,
        },
    )
    assert rag_resp.status_code == 200
    data = rag_resp.json()

    meta = data["retrieval_metadata"]
    assert meta["dense_candidates_count"] > 0
    assert meta["sparse_candidates_count"] > 0
    assert meta["merged_candidates_count"] > 0
    assert not meta["is_abstention"]
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["page_number"] == 2
