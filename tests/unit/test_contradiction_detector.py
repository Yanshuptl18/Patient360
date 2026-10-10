"""Unit tests for clinical contradiction detector."""

from datetime import date
from unittest.mock import MagicMock

from backend.models.timeline import ClinicalEvent
from backend.timeline.contradictions import ContradictionDetector


def _create_mock_event(
    id: str,
    doc_id: str,
    doc_title: str,
    event_type: str,
    description: str,
    event_date: date,
    value_or_dosage: str | None = None,
    clinical_status: str = "active",
) -> ClinicalEvent:
    ev = ClinicalEvent(
        id=id,
        patient_id="pat-1",
        document_id=doc_id,
        chunk_id=f"chk-{id}",
        event_type=event_type,
        event_date=event_date,
        event_date_precision="day",
        document_date=event_date,
        description=description,
        value_or_dosage=value_or_dosage,
        clinical_status=clinical_status,
        confidence_score=1.0,
        contradiction_flag=False,
    )
    mock_doc = MagicMock()
    mock_doc.title = doc_title
    ev.document = mock_doc
    mock_chunk = MagicMock()
    mock_chunk.page_number = 1
    ev.chunk = mock_chunk
    return ev


def test_detect_allergy_vs_nkda_conflict() -> None:
    detector = ContradictionDetector()

    ev1 = _create_mock_event(
        id="ev-1",
        doc_id="doc-1",
        doc_title="Inpatient_Admission_2023.pdf",
        event_type="allergy",
        description="No known drug allergies (NKDA)",
        event_date=date(2023, 1, 10),
    )

    ev2 = _create_mock_event(
        id="ev-2",
        doc_id="doc-2",
        doc_title="Discharge_Summary_2021.pdf",
        event_type="allergy",
        description="Penicillin Allergy",
        event_date=date(2021, 4, 12),
        value_or_dosage="Severe anaphylaxis",
    )

    conflicts = detector.detect_contradictions([ev1, ev2])
    assert len(conflicts) == 1
    c = conflicts[0]
    assert c.conflict_type == "allergy_conflict"
    assert c.severity == "critical"
    assert ev1.contradiction_flag is True
    assert ev2.contradiction_flag is True
    assert "NKDA" in (ev1.contradiction_details or "")


def test_detect_allergy_vs_active_medication_conflict() -> None:
    detector = ContradictionDetector()

    allergy_ev = _create_mock_event(
        id="ev-allg",
        doc_id="doc-1",
        doc_title="Discharge_Summary_2021.pdf",
        event_type="allergy",
        description="Lisinopril Allergy",
        event_date=date(2021, 4, 12),
        value_or_dosage="Facial angioedema",
    )

    med_ev = _create_mock_event(
        id="ev-med",
        doc_id="doc-2",
        doc_title="Clinic_Followup_2023.pdf",
        event_type="medication",
        description="Lisinopril Therapy",
        event_date=date(2023, 5, 20),
        value_or_dosage="10mg daily",
    )

    conflicts = detector.detect_contradictions([allergy_ev, med_ev])
    assert len(conflicts) == 1
    assert conflicts[0].severity == "critical"
    assert allergy_ev.contradiction_flag is True
    assert med_ev.contradiction_flag is True


def test_detect_procedure_date_discrepancy() -> None:
    detector = ContradictionDetector()

    p1 = _create_mock_event(
        id="p-1",
        doc_id="doc-1",
        doc_title="Surgical_Consult_2020.pdf",
        event_type="procedure",
        description="Appendectomy",
        event_date=date(2018, 1, 1),
    )

    p2 = _create_mock_event(
        id="p-2",
        doc_id="doc-2",
        doc_title="Emergency_Note_2023.pdf",
        event_type="procedure",
        description="Appendectomy",
        event_date=date(2021, 6, 15),
    )

    conflicts = detector.detect_contradictions([p1, p2])
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "date_conflict"
    assert conflicts[0].severity == "moderate"
    assert p1.contradiction_flag is True
    assert p2.contradiction_flag is True


def test_no_contradiction_for_consistent_events() -> None:
    detector = ContradictionDetector()

    ev1 = _create_mock_event(
        id="ev-1",
        doc_id="doc-1",
        doc_title="Note_1.pdf",
        event_type="diagnosis",
        description="Type 2 Diabetes Mellitus",
        event_date=date(2020, 1, 1),
    )

    ev2 = _create_mock_event(
        id="ev-2",
        doc_id="doc-2",
        doc_title="Note_2.pdf",
        event_type="medication",
        description="Metformin Therapy",
        event_date=date(2020, 1, 5),
        value_or_dosage="500mg BID",
    )

    conflicts = detector.detect_contradictions([ev1, ev2])
    assert len(conflicts) == 0
    assert ev1.contradiction_flag is False
    assert ev2.contradiction_flag is False
