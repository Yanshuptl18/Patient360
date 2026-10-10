"""Unit tests for timeline chronological sorting, filters, and summary metrics."""

from datetime import date
from unittest.mock import MagicMock

from backend.models.timeline import ClinicalEvent
from backend.timeline.service import TimelineService


def test_timeline_sorting_and_filtering() -> None:
    service = TimelineService()

    # Mock DB Session
    mock_db = MagicMock()

    mock_patient = MagicMock()
    mock_patient.id = "pat-1"
    mock_patient.first_name = "Eleanor"
    mock_patient.last_name = "Vance"

    mock_db.query.return_value.filter.return_value.first.return_value = mock_patient
    mock_db.query.return_value.filter.return_value.count.return_value = 3

    # Create mock events on different dates
    e1 = ClinicalEvent(
        id="e-1",
        patient_id="pat-1",
        document_id="d-1",
        event_type="diagnosis",
        event_date=date(2020, 1, 15),
        event_date_precision="day",
        description="Type 2 Diabetes Mellitus",
        clinical_status="active",
        confidence_score=1.0,
    )
    e1.document = MagicMock(title="Consult_2020.pdf")
    e1.chunk = MagicMock(page_number=1, raw_content="Diagnosed with Type 2 Diabetes.")

    e2 = ClinicalEvent(
        id="e-2",
        patient_id="pat-1",
        document_id="d-2",
        event_type="procedure",
        event_date=date(2018, 5, 20),
        event_date_precision="day",
        description="Appendectomy",
        clinical_status="historical",
        confidence_score=1.0,
    )
    e2.document = MagicMock(title="Surgery_2018.pdf")
    e2.chunk = MagicMock(page_number=1, raw_content="Appendectomy performed in 2018.")

    e3 = ClinicalEvent(
        id="e-3",
        patient_id="pat-1",
        document_id="d-3",
        event_type="lab_result",
        event_date=date(2023, 8, 10),
        event_date_precision="day",
        description="Lab: HbA1c",
        value_or_dosage="6.2%",
        clinical_status="active",
        confidence_score=1.0,
    )
    e3.document = MagicMock(title="Labs_2023.pdf")
    e3.chunk = MagicMock(page_number=2, raw_content="HbA1c level measured at 6.2%.")

    events_list = [e2, e1, e3]  # Chronological order: 2018, 2020, 2023

    # Configure query chain
    mock_query = MagicMock()
    mock_query.options.return_value.filter.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value.all.return_value = events_list
    mock_query.all.return_value = events_list

    mock_db.query.return_value = mock_query
    mock_db.query.return_value.filter.return_value.first.return_value = mock_patient
    mock_db.query.return_value.filter.return_value.count.return_value = 3

    resp = service.get_patient_timeline(db=mock_db, patient_id="pat-1", order="asc")

    assert resp.patient_id == "pat-1"
    assert resp.patient_name == "Eleanor Vance"
    assert resp.summary.total_events == 3
    assert resp.summary.earliest_date == date(2018, 5, 20)
    assert resp.summary.latest_date == date(2023, 8, 10)
    assert resp.summary.event_counts_by_type["procedure"] == 1
    assert resp.summary.event_counts_by_type["diagnosis"] == 1
    assert resp.summary.event_counts_by_type["lab_result"] == 1
