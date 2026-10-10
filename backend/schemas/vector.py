"""Pydantic schemas for vector search operations and statistics."""

from pydantic import BaseModel, Field


class VectorSearchRequest(BaseModel):
    """Payload for dense vector similarity queries."""

    query: str = Field(..., min_length=1, description="Natural language clinical search query")
    patient_id: str | None = Field(default=None, description="Optional patient ID to isolate search")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of candidate chunks to retrieve")
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum cosine similarity cutoff")


class VectorSearchResultItem(BaseModel):
    """Individual vector search match with cosine score and page provenance."""

    chunk_id: str
    document_id: str
    patient_id: str | None
    page_number: int
    chunk_index: int
    content: str
    raw_content: str
    score: float
    doc_title: str
    doc_type: str
    doc_date: str | None


class VectorStatsResponse(BaseModel):
    """Qdrant collection status and vector counts."""

    collection_name: str
    status: str
    vectors_count: int
    indexed_vectors_count: int
    dimensions: int
    is_embedded: bool


class HybridSearchRequest(BaseModel):
    """Payload for hybrid (dense vector + sparse BM25 + RRF) retrieval."""

    query: str = Field(..., min_length=1, description="Natural language clinical search query")
    patient_id: str = Field(..., description="Patient ID to isolate search")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of merged candidates to return")
    rrf_k: int = Field(default=60, ge=1, le=200, description="RRF smoothing constant")


class HybridSearchResultItem(BaseModel):
    """Ranked candidate merged using Reciprocal Rank Fusion."""

    chunk_id: str
    document_id: str
    patient_id: str | None
    page_number: int
    chunk_index: int
    content: str
    raw_content: str
    rrf_score: float
    dense_rank: int | None
    sparse_rank: int | None
    dense_score: float | None
    sparse_score: float | None
    doc_title: str
    doc_type: str
    doc_date: str | None
