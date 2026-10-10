"""Pydantic schemas for longitudinal clinical events, timeline responses, and contradictions."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ClinicalEventType = Literal[
    "diagnosis",
    "medication",
    "procedure",
    "encounter",
    "lab_result",
    "allergy",
]

DatePrecision = Literal["day", "month", "year", "approximate"]

ClinicalStatus = Literal["active", "historical", "resolved", "disputed"]

ContradictionSeverity = Literal["critical", "moderate", "minor"]

ContradictionConflictType = Literal[
    "allergy_conflict",
    "status_conflict",
    "date_conflict",
    "value_conflict",
    "general_conflict",
]


class ClinicalEventBase(BaseModel):
    """Base schema for clinical event entity."""

    event_type: ClinicalEventType
    event_date: date
    event_date_precision: DatePrecision = "day"
    document_date: date | None = None
    description: str = Field(..., min_length=2, max_length=2000)
    value_or_dosage: str | None = Field(default=None, max_length=255)
    clinical_status: ClinicalStatus = "active"
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    contradiction_flag: bool = False
    contradiction_details: str | None = None


class ClinicalEventCreate(ClinicalEventBase):
    """Payload for creating an extracted clinical event."""

    patient_id: str
    document_id: str
    chunk_id: str | None = None


class ClinicalEventResponse(ClinicalEventBase):
    """Response schema representing a saved clinical event with provenance."""

    id: str
    patient_id: str
    document_id: str
    chunk_id: str | None = None
    created_at: datetime

    # Provenance fields populated from relations
    document_title: str | None = None
    page_number: int | None = None
    exact_quote: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ContradictionItem(BaseModel):
    """Detailed clinical contradiction or conflict surfaced between documentation."""

    event_id_1: str
    event_id_2: str
    event_1_summary: str
    event_2_summary: str
    document_title_1: str
    document_title_2: str
    page_number_1: int | None = None
    page_number_2: int | None = None
    conflict_type: ContradictionConflictType
    severity: ContradictionSeverity
    explanation: str
    suggested_resolution: str | None = None


class TimelineSummary(BaseModel):
    """Statistical summary of patient's longitudinal trajectory."""

    total_events: int
    event_counts_by_type: dict[str, int]
    earliest_date: date | None = None
    latest_date: date | None = None
    total_contradictions: int = 0


class PatientTimelineResponse(BaseModel):
    """Complete longitudinal timeline response for a patient dossier."""

    patient_id: str
    patient_name: str
    summary: TimelineSummary
    contradictions: list[ContradictionItem]
    events: list[ClinicalEventResponse]


class TimelineExtractRequest(BaseModel):
    """Request to trigger or refresh timeline event extraction."""

    patient_id: str
    document_ids: list[str] | None = None
    force_reextract: bool = False


class TimelineExtractResponse(BaseModel):
    """Response returned upon completion of event extraction and contradiction analysis."""

    patient_id: str
    events_extracted_count: int
    contradictions_detected_count: int
    documents_processed_count: int
    status: str = "COMPLETED"
    message: str
