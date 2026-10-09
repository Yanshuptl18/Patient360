"""Integration tests for vector indexing, semantic search, and patient isolation."""

import io

import pymupdf
from fastapi.testclient import TestClient


def create_sample_medical_pdf() -> bytes:
    """Creates a sample multi-page medical PDF with distinct findings on each page."""
    doc = pymupdf.open()
    # Page 1: History
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 72),
        "PULMONARY CLINIC CONSULTATION\nPatient: Eleanor Vance\n"
        "History of Present Illness: Patient presents with persistent non-productive cough "
        "and progressive dyspnea on exertion. Non-smoker.",
        fontsize=11,
    )
    # Page 2: Pathology & Molecular Biomarkers
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(
        (50, 72),
        "MOLECULAR PATHOLOGY REPORT\nSpecimen: Right upper lobe lung biopsy\n"
        "Diagnosis: Invasive lung adenocarcinoma.\n"
        "Molecular Genetics: Next-generation sequencing identified EGFR L858R point mutation in exon 21.\n"
        "PD-L1 Expression: TPS 45%. ALK and ROS1 rearrangements negative.",
        fontsize=11,
    )
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_end_to_end_vector_indexing_and_search(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies end-to-end vector indexing and precise page-attributed semantic search."""
    headers = reviewer_headers

    # 1. Create Patient
    p_resp = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-VEC-01",
            "first_name": "Eleanor",
            "last_name": "Vance",
            "date_of_birth": "1975-08-20",
            "gender": "Female",
            "primary_condition": "Adenocarcinoma",
        },
        headers=headers,
    )
    assert p_resp.status_code == 201
    patient_id = p_resp.json()["id"]

    # 2. Upload Document
    pdf_bytes = create_sample_medical_pdf()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("pathology_report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={
            "title": "Molecular Pathology Report",
            "doc_type": "lab_report",
            "doc_date": "2024-05-10",
            "patient_id": patient_id,
        },
        headers=headers,
    )
    assert upload_resp.status_code == 202
    doc_id = upload_resp.json()["document_id"]

    # 3. Ingest and vector index document
    ingest_resp = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)
    assert ingest_resp.status_code == 200
    assert ingest_resp.json()["status"] == "completed"

    # 4. Check Vector Store Stats API
    stats_resp = client.get("/api/v1/vector/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["status"] == "UP"
    assert stats["dimensions"] == 384
    assert stats["vectors_count"] >= 2

    # 5. Search for Molecular Mutation Finding
    search_resp = client.post(
        "/api/v1/vector/search",
        json={
            "query": "EGFR L858R point mutation in exon 21",
            "patient_id": patient_id,
            "top_k": 3,
        },
        headers=headers,
    )
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) >= 1

    top_hit = results[0]
    assert top_hit["patient_id"] == patient_id
    assert top_hit["page_number"] == 2  # The mutation was on Page 2!
    assert "EGFR L858R" in top_hit["content"]
    assert top_hit["score"] > 0.60
    assert "[Document: Molecular Pathology Report | Page: 2" in top_hit["content"]


def test_vector_search_patient_isolation_and_rbac(
    client: TestClient,
    reviewer_headers: dict[str, str],
    researcher_headers: dict[str, str],
) -> None:
    """Verifies that vector search strictly isolates patient records and enforces RBAC."""
    # Reviewer creates Patient Alpha
    p_alpha = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-VEC-ALPHA",
            "first_name": "Alpha",
            "last_name": "Patient",
            "date_of_birth": "1980-01-01",
            "gender": "Male",
        },
        headers=reviewer_headers,
    ).json()

    # Reviewer creates Patient Beta
    p_beta = client.post(
        "/api/v1/patients",
        json={
            "mrn_synthetic": "SYN-VEC-BETA",
            "first_name": "Beta",
            "last_name": "Patient",
            "date_of_birth": "1985-02-02",
            "gender": "Female",
        },
        headers=reviewer_headers,
    ).json()

    # Upload and ingest doc for Alpha
    pdf_bytes = create_sample_medical_pdf()
    up = client.post(
        "/api/v1/documents/upload",
        files={"file": ("alpha.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"title": "Alpha Report", "patient_id": p_alpha["id"]},
        headers=reviewer_headers,
    ).json()
    client.post(f"/api/v1/documents/{up['document_id']}/ingest", headers=reviewer_headers)

    # Searching with patient_id=Beta must yield 0 results
    search_beta = client.post(
        "/api/v1/vector/search",
        json={
            "query": "EGFR mutation",
            "patient_id": p_beta["id"],
        },
        headers=reviewer_headers,
    )
    assert search_beta.status_code == 200
    assert len(search_beta.json()) == 0

    # Researcher searching for Alpha must be rejected with 403 Forbidden
    search_unauthorized = client.post(
        "/api/v1/vector/search",
        json={
            "query": "EGFR mutation",
            "patient_id": p_alpha["id"],
        },
        headers=researcher_headers,
    )
    assert search_unauthorized.status_code == 403
