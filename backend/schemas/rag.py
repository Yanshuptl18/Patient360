"""Pydantic schemas for Grounded RAG query, citation metadata, and user feedback."""

from typing import Literal

from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    """Request payload for evidence-grounded question answering."""

    query: str = Field(..., min_length=2, max_length=1000, description="Clinical query or question.")
    patient_id: str = Field(..., description="ID of patient dossier to retrieve evidence from.")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of context chunks to retrieve.")


class CitationItem(BaseModel):
    """Detailed attribution metadata for an evidence citation."""

    document_id: str
    document_title: str
    page_number: int
    exact_quote: str
    claim_text: str
    verification_status: Literal["supported", "partially_supported", "unsupported"]


class RetrievalMetadata(BaseModel):
    """Performance telemetry and candidate counts for the RAG query."""

    dense_candidates_count: int
    merged_candidates_count: int
    retrieval_latency_ms: int
    generation_latency_ms: int
    total_latency_ms: int
    is_abstention: bool


class RAGQueryResponse(BaseModel):
    """Evidence-grounded synthesized response with page-level citations."""

    query: str
    patient_id: str
    answer: str
    citations: list[CitationItem]
    limitations: list[str]
    confidence_score: float
    retrieval_metadata: RetrievalMetadata


class RAGFeedbackRequest(BaseModel):
    """Clinician or researcher feedback on synthesized RAG answer."""

    patient_id: str
    query: str
    answer: str
    rating: Literal["positive", "negative"]
    issue_type: str | None = Field(
        None,
        description="Optional category of issue: e.g. contradiction_unnoticed, hallucination, missing_source.",
    )
    comment: str | None = Field(None, max_length=1000, description="Optional qualitative clinician feedback.")


class RAGFeedbackResponse(BaseModel):
    """Response acknowledging logged user feedback."""

    status: str
    message: str
