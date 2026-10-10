"""Integration tests for longitudinal patient timeline extraction, queries, and contradiction surfacing."""

import io

import pymupdf
from fastapi.testclient import TestClient


def create_discharge_summary_pdf() -> bytes:
    """PDF 1: Documents severe Lisinopril allergy and 2018 appendectomy."""
    doc = pymupdf.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 72),
        "DISCHARGE SUMMARY\n"
        "Document Date: 2021-04-14\n"
        "Patient: Eleanor Vance (MRN: SYN-TIME-001)\n\n"
        "Allergies: Lisinopril, reaction: severe facial angioedema observed on 2021-04-12.\n"
        "Past Surgical History: Underwent Appendectomy in 2018.\n"
        "Assessment: Acute decompensated heart failure with pulmonary congestion.\n"
        "Hospital Course: Patient stabilized with IV diuretics.",
        fontsize=11,
    )
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def create_clinic_followup_pdf() -> bytes:
    """PDF 2: Documents Lisinopril as active medication and 2021 appendectomy (contradictions)."""
    doc = pymupdf.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 72),
        "OUTPATIENT CLINIC CONSULTATION NOTE\n"
        "Document Date: 2023-01-15\n"
        "Patient: Eleanor Vance (MRN: SYN-TIME-001)\n\n"
        "Active Medications: Lisinopril 10mg daily, Metformin 500mg BID.\n"
        "Surgical History: Appendectomy performed in 2021.\n"
        "Assessment: Congestive heart failure, NYHA Class II.",
        fontsize=11,
    )
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_timeline_extraction_and_contradiction_pipeline(
    client: TestClient, reviewer_headers: dict[str, str]
) -> None:
    headers = reviewer_headers

    # 1. Register synthetic patient
    patient_resp = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "mrn_synthetic": "SYN-TIME-001",
            "first_name": "Eleanor",
            "last_name": "Vance",
            "date_of_birth": "1965-04-20",
            "gender": "female",
            "primary_condition": "Heart Failure",
        },
    )
    assert patient_resp.status_code == 201
    patient_id = patient_resp.json()["id"]

    # 2. Upload and ingest Document 1
    pdf1 = create_discharge_summary_pdf()
    up1 = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "title": "Discharge_Summary_2021.pdf",
            "doc_type": "discharge_summary",
            "doc_date": "2021-04-14",
        },
        files={"file": ("Discharge_Summary_2021.pdf", io.BytesIO(pdf1), "application/pdf")},
    )
    assert up1.status_code == 202
    doc1_id = up1.json()["document_id"]

    ing1 = client.post(f"/api/v1/documents/{doc1_id}/ingest", headers=headers)
    assert ing1.status_code == 200

    # 3. Upload and ingest Document 2
    pdf2 = create_clinic_followup_pdf()
    up2 = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "title": "Clinic_Note_2023.pdf",
            "doc_type": "patient_record",
            "doc_date": "2023-01-15",
        },
        files={"file": ("Clinic_Note_2023.pdf", io.BytesIO(pdf2), "application/pdf")},
    )
    assert up2.status_code == 202
    doc2_id = up2.json()["document_id"]

    ing2 = client.post(f"/api/v1/documents/{doc2_id}/ingest", headers=headers)
    assert ing2.status_code == 200

    # 4. Fetch Timeline via API
    timeline_resp = client.get(
        f"/api/v1/timeline/patients/{patient_id}",
        headers=headers,
    )
    assert timeline_resp.status_code == 200
    timeline_data = timeline_resp.json()

    assert timeline_data["patient_id"] == patient_id
    assert timeline_data["patient_name"] == "Eleanor Vance"
    events = timeline_data["events"]
    assert len(events) >= 4

    # Verify chronological sorting (default asc)
    event_dates = [e["event_date"] for e in events]
    assert event_dates == sorted(event_dates)

    # 5. Verify Contradictions surfaced
    contradictions = timeline_data["contradictions"]
    assert len(contradictions) >= 2

    # Check Lisinopril allergy vs active prescription contradiction
    lisinopril_conflict = [
        c
        for c in contradictions
        if "Lisinopril" in c["event_1_summary"] or "Lisinopril" in c["event_2_summary"]
    ]
    assert len(lisinopril_conflict) >= 1
    assert lisinopril_conflict[0]["severity"] == "critical"
    assert lisinopril_conflict[0]["conflict_type"] == "allergy_conflict"

    # Check Appendectomy date conflict (2018 vs 2021)
    app_conflict = [c for c in contradictions if c["conflict_type"] == "date_conflict"]
    assert len(app_conflict) >= 1
    assert app_conflict[0]["severity"] == "moderate"

    # 6. Test Contradictions endpoint directly
    contra_resp = client.get(
        f"/api/v1/timeline/patients/{patient_id}/contradictions",
        headers=headers,
    )
    assert contra_resp.status_code == 200
    assert len(contra_resp.json()) >= 2


def test_timeline_unauthorized_cross_patient_rejection(
    client: TestClient, researcher_headers: dict[str, str], reviewer_headers: dict[str, str]
) -> None:
    """Verifies that non-permitted users receive 403 Forbidden on patient timeline endpoints."""
    # Register patient with reviewer account
    patient_resp = client.post(
        "/api/v1/patients",
        headers=reviewer_headers,
        json={
            "mrn_synthetic": "SYN-SECRET-001",
            "first_name": "Private",
            "last_name": "Patient",
            "date_of_birth": "1970-01-01",
            "gender": "female",
        },
    )
    patient_id = patient_resp.json()["id"]

    # Attempt to read timeline with researcher account (unpermitted)
    resp = client.get(
        f"/api/v1/timeline/patients/{patient_id}",
        headers=researcher_headers,
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"
