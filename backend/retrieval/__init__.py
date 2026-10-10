"""Retrieval package combining dense vector retrieval, in-memory BM25, and Reciprocal Rank Fusion."""

from backend.retrieval.bm25 import (
    BM25Document,
    BM25Index,
    BM25SearchResult,
    PatientBM25Registry,
    get_bm25_registry,
    tokenize_clinical_text,
)
from backend.retrieval.rrf import (
    DEFAULT_RRF_K,
    HybridSearchResult,
    reciprocal_rank_fusion,
)
from backend.retrieval.service import (
    HybridRetrievalService,
    get_hybrid_retrieval_service,
)

__all__ = [
    "BM25Document",
    "BM25Index",
    "BM25SearchResult",
    "PatientBM25Registry",
    "get_bm25_registry",
    "tokenize_clinical_text",
    "DEFAULT_RRF_K",
    "HybridSearchResult",
    "reciprocal_rank_fusion",
    "HybridRetrievalService",
    "get_hybrid_retrieval_service",
]
