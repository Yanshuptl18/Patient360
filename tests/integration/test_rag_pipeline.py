"""Integration tests for end-to-end Grounded RAG query, abstention, and feedback."""

import io

import pymupdf
from fastapi.testclient import TestClient


def create_sample_oncology_pdf() -> bytes:
    """Creates a 2-page clinical report with specific pathology findings."""
    doc = pymupdf.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 72),
        "PULMONARY CONSULTATION NOTE\nPatient: Eleanor Vance (MRN: SYN-RAG-01)\n"
        "Chief Complaint: Progressive dyspnea and persistent cough for 6 weeks.\n"
        "Assessment: High clinical suspicion for primary lung malignancy. Biopsy ordered.",
        fontsize=11,
    )

    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(
        (50, 72),
        "SURGICAL PATHOLOGY & MOLECULAR GENETICS REPORT\n"
        "Specimen: CT-guided right lung biopsy.\n"
        "Histologic Diagnosis: Invasive lung adenocarcinoma.\n"
        "Molecular Genetics: Next-generation sequencing identified EGFR L858R mutation in exon 21.\n"
        "PD-L1 Expression: TPS 45%. ALK and ROS1 rearrangements negative.",
        fontsize=11,
    )
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_end_to_end_grounded_rag_query(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies that RAG returns a grounded answer with page-level citations for supported queries."""
    headers = reviewer_headers

    # 1. Register patient
    patient_resp = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "mrn_synthetic": "SYNTH-RAG-001",
            "first_name": "Eleanor",
            "last_name": "Vance",
            "date_of_birth": "1968-04-12",
            "gender": "female",
            "primary_condition": "Non-Small Cell Lung Cancer",
        },
    )
    assert patient_resp.status_code == 201
    patient_id = patient_resp.json()["id"]

    # 2. Upload sample oncology PDF
    pdf_content = create_sample_oncology_pdf()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "title": "Oncology_Pathology_Report.pdf",
            "doc_type": "lab_report",
            "doc_date": "2024-03-20",
        },
        files={"file": ("Oncology_Pathology_Report.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert upload_resp.status_code == 202
    doc_id = upload_resp.json()["document_id"]

    # 3. Trigger document ingestion and Qdrant indexing
    ingest_resp = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)
    assert ingest_resp.status_code == 200
    assert ingest_resp.json()["status"] == "completed"

    # 4. Perform grounded RAG query for molecular mutation
    rag_resp = client.post(
        "/api/v1/rag/query",
        headers=headers,
        json={
            "query": "What EGFR mutation was detected in this patient's biopsy?",
            "patient_id": patient_id,
            "top_k": 5,
        },
    )
    assert rag_resp.status_code == 200
    data = rag_resp.json()

    assert data["patient_id"] == patient_id
    assert not data["retrieval_metadata"]["is_abstention"]
    assert "EGFR" in data["answer"]
    assert len(data["citations"]) >= 1

    citation = data["citations"][0]
    assert citation["document_id"] == doc_id
    assert citation["page_number"] == 2
    assert citation["verification_status"] == "supported"
    assert "EGFR L858R" in citation["exact_quote"] or "EGFR" in citation["exact_quote"]
    assert data["confidence_score"] > 0.5


def test_rag_abstention_on_unsupported_facts(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies that RAG deterministically abstains when facts are not in patient records."""
    headers = reviewer_headers

    # Register patient with no documents or irrelevant documents
    patient_resp = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "mrn_synthetic": "SYNTH-RAG-002",
            "first_name": "Marcus",
            "last_name": "Brody",
            "date_of_birth": "1972-11-05",
            "gender": "male",
        },
    )
    assert patient_resp.status_code == 201
    patient_id = patient_resp.json()["id"]

    # Inquire about penicillin anaphylaxis (not documented)
    rag_resp = client.post(
        "/api/v1/rag/query",
        headers=headers,
        json={
            "query": "Does Marcus have documented penicillin anaphylaxis?",
            "patient_id": patient_id,
            "top_k": 5,
        },
    )
    assert rag_resp.status_code == 200
    data = rag_resp.json()

    assert data["retrieval_metadata"]["is_abstention"] is True
    assert "Insufficient evidence documented in available records." in data["answer"]
    assert len(data["citations"]) == 0
    assert data["confidence_score"] == 0.0


def test_rag_cross_patient_authorization_rejected(
    client: TestClient, admin_headers: dict[str, str], reviewer_headers: dict[str, str]
) -> None:
    """Verifies that non-permitted clinicians cannot query unauthorized patient dossiers."""
    # Admin creates a private patient dossier
    patient_resp = client.post(
        "/api/v1/patients",
        headers=admin_headers,
        json={
            "mrn_synthetic": "SYNTH-RAG-003",
            "first_name": "Classified",
            "last_name": "VIP",
            "date_of_birth": "1960-01-01",
            "gender": "other",
        },
    )
    assert patient_resp.status_code == 201
    patient_id = patient_resp.json()["id"]

    # Reviewer attempts to query this dossier without permission
    rag_resp = client.post(
        "/api/v1/rag/query",
        headers=reviewer_headers,
        json={
            "query": "What are the patient's medications?",
            "patient_id": patient_id,
        },
    )
    assert rag_resp.status_code == 403


def test_rag_feedback_submission(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    """Verifies that clinicians can submit feedback on RAG answers."""
    headers = reviewer_headers

    patient_resp = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "mrn_synthetic": "SYNTH-RAG-004",
            "first_name": "Clara",
            "last_name": "Oswald",
            "date_of_birth": "1986-11-23",
            "gender": "female",
        },
    )
    assert patient_resp.status_code == 201
    patient_id = patient_resp.json()["id"]

    feedback_resp = client.post(
        "/api/v1/rag/feedback",
        headers=headers,
        json={
            "patient_id": patient_id,
            "query": "What was the biopsy result?",
            "answer": "Adenocarcinoma EGFR L858R.",
            "rating": "positive",
            "issue_type": None,
            "comment": "Accurately extracted mutation and page number.",
        },
    )
    assert feedback_resp.status_code == 201
    assert feedback_resp.json()["status"] == "FEEDBACK_LOGGED"
