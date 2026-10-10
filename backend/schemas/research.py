"""Pydantic schemas for medical research intelligence and study comparison matrices."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EvidenceStrength = Literal["High", "Moderate", "Low-Moderate", "Preliminary"]


class ResearchStudyBase(BaseModel):
    """Base schema for extracted biomedical research study."""

    pmid: str | None = Field(default=None, max_length=32)
    doi: str | None = Field(default=None, max_length=128)
    title: str = Field(..., min_length=3, max_length=1000)
    authors: str | None = Field(default=None, max_length=1000)
    publication_date: date | None = None
    study_design: str | None = Field(default=None, max_length=100)
    population_description: str | None = None
    sample_size: int | None = Field(default=None, ge=1)
    intervention: str | None = None
    primary_outcome: str | None = None
    limitations: str | None = None


class ResearchStudyCreate(ResearchStudyBase):
    """Payload to create or persist an extracted study."""

    document_id: str


class ResearchStudyResponse(ResearchStudyBase):
    """Response representation of an indexed research study."""

    id: str
    document_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudyExtractRequest(BaseModel):
    """Request payload to trigger parameter extraction from an uploaded publication."""

    document_id: str


class StudyCompareRequest(BaseModel):
    """Payload to construct a structured Evidence Comparison Matrix."""

    study_ids: list[str] = Field(..., min_length=1, max_length=10)
    comparison_topic: str | None = Field(default=None, max_length=500)


class StudyMatrixRow(BaseModel):
    """Side-by-side comparative parameter row for an individual study."""

    study_id: str
    title: str
    doi: str | None = None
    pmid: str | None = None
    authors: str | None = None
    publication_year: int | None = None
    study_design: str | None = None
    sample_size: int | None = None
    population: str | None = None
    intervention: str | None = None
    primary_outcome: str | None = None
    limitations: str | None = None
    evidence_strength: EvidenceStrength


class StudyComparisonMatrix(BaseModel):
    """Evidence Comparison Matrix contrasting multiple research studies side-by-side."""

    comparison_topic: str
    studies_count: int
    matrix_rows: list[StudyMatrixRow]
    synthesized_findings: str
    guideline_alignment: str | None = None


class DossierExportRequest(BaseModel):
    """Request payload to generate and export an evidence synthesis dossier."""

    study_ids: list[str] = Field(..., min_length=1, max_length=10)
    comparison_topic: str | None = Field(default=None, max_length=500)
    title: str | None = Field(default=None, max_length=255)


class DossierExportResponse(BaseModel):
    """Formatted synthesis dossier payload."""

    title: str
    markdown_content: str
    studies_included_count: int
    generated_at_iso: str
