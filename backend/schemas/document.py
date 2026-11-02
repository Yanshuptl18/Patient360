"""Pydantic schemas for Document operations."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class DocTypeEnum(StrEnum):
    PATIENT_RECORD = "patient_record"
    LAB_REPORT = "lab_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    RESEARCH_PAPER = "research_paper"
    CLINICAL_GUIDELINE = "clinical_guideline"


class IngestionStatusEnum(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERY_REQUIRED = "recovery_required"


class DocumentResponse(BaseModel):
    id: str
    patient_id: str | None
    title: str
    file_hash_sha256: str | None = None
    file_size_bytes: int
    mime_type: str
    doc_type: str
    doc_date: date | None
    ingestion_status: str
    error_message: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    message: str
    file_hash_sha256: str
    file_size_bytes: int


class IngestionJobResponse(BaseModel):
    id: str
    document_id: str
    patient_id: str | None
    status: str
    attempts: int
    max_attempts: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
