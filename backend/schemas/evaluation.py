"""Pydantic schemas for evaluation benchmark runs, category breakdowns, and metrics."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkCategory(StrEnum):
    """The categories defined for clinical evaluation benchmarks."""

    # Core evaluation categories
    SINGLE_DOC_FACTUAL = "single_doc_factual"
    MULTI_DOC_LONGITUDINAL = "multi_doc_longitudinal"
    CONTRADICTORY_RECORDS = "contradictory_records"
    UNANSWERABLE_ABSTENTION = "unanswerable_abstention"
    ADVERSARIAL_INJECTION = "adversarial_injection"
    RESEARCH_MATRIX = "research_matrix"

    # Expanded 15 clinical challenge categories
    MEDICATION_DOSAGE = "medication_dosage"
    MEDICATION_CONTRAINDICATION = "medication_contraindication"
    TEMPORAL_TRAJECTORIES = "temporal_trajectories"
    CROSS_DOCUMENT_CONTRADICTIONS = "cross_document_contradictions"
    SCANNED_OCR_EXTRACTION = "scanned_ocr_extraction"
    LABORATORY_INTERPRETATION = "laboratory_interpretation"
    CLINICAL_ABSTENTION = "clinical_abstention"
    ADVERSARIAL_INJECTIONS = "adversarial_injections"
    PEDIATRIC_GERIATRIC_CONTEXT = "pediatric_geriatric_context"
    DIAGNOSTIC_CRITERIA = "diagnostic_criteria"
    EMERGENCY_TRIAGE = "emergency_triage"
    PROCEDURE_HISTORY = "procedure_history"
    ALLERGY_CONFLICT = "allergy_conflict"
    UNANSWERABLE_MISSING_EVIDENCE = "unanswerable_missing_evidence"
    MULTI_CONDITION_SYNTHESIS = "multi_condition_synthesis"


class EvaluationBenchmarkItem(BaseModel):
    """Curated frozen synthetic benchmark test item definition."""

    id: str
    category: BenchmarkCategory
    title: str
    query: str
    patient_id: str | None = None
    expected_golden_chunk_ids: list[str] = Field(default_factory=list)
    expected_answer_keywords: list[str] = Field(default_factory=list)
    forbidden_keywords: list[str] = Field(default_factory=list)
    should_abstain: bool = False
    has_contradiction: bool = False
    is_adversarial: bool = False

    model_config = ConfigDict(from_attributes=True)


class EvaluationItemResult(BaseModel):
    """Detailed score evaluation for an individual benchmark item."""

    item_id: str
    category: str
    query: str
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    generated_answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    hit_at_5: bool
    reciprocal_rank: float
    faithfulness_score: float
    citation_precision_score: float
    abstention_correct: bool
    passed: bool
    retrieval_latency_ms: float
    e2e_latency_ms: float
    failure_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


class EvaluationCategorySummary(BaseModel):
    """Aggregated performance metrics for a specific benchmark category."""

    category: str
    category_label: str
    total_items: int
    passed_items: int
    pass_rate: float
    avg_faithfulness: float
    avg_citation_precision: float
    avg_mrr: float

    model_config = ConfigDict(from_attributes=True)


class EvaluationRunRequest(BaseModel):
    """Request payload to trigger an automated or interactive benchmark evaluation run."""

    name: str = Field(
        default="Synthetic Clinical Benchmark (50 items)",
        description="Descriptive identifier for the benchmark execution.",
    )
    mode: str = Field(
        default="hybrid",
        description="Retrieval mode: 'hybrid' (RRF), 'dense_only', or 'sparse_only'.",
    )
    limit: int | None = Field(
        default=None,
        ge=1,
        le=50,
        description="Optional limit to run a subset of items (default runs all 50).",
    )


class EvaluationRunSummary(BaseModel):
    """Lightweight summary of an evaluation run for historical trend listings."""

    id: str
    name: str
    git_commit: str
    mode: str
    total_items: int
    passed_items: int
    recall_at_5: float
    mrr: float
    faithfulness: float
    citation_precision: float
    abstention_accuracy: float
    p95_retrieval_latency_ms: float
    p95_e2e_latency_ms: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationRunResponse(EvaluationRunSummary):
    """Comprehensive evaluation run report including detailed item results and category summaries."""

    summary_metrics: dict[str, Any] = Field(default_factory=dict)
    item_results: list[EvaluationItemResult] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
