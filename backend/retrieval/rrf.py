"""Reciprocal Rank Fusion (RRF) for merging dense vector and sparse BM25 candidate lists."""

from dataclasses import dataclass
from typing import Any

from backend.retrieval.bm25 import BM25SearchResult
from backend.vector.store import VectorSearchResult

DEFAULT_RRF_K = 60


@dataclass
class HybridSearchResult:
    """Consolidated search candidate resulting from Reciprocal Rank Fusion."""

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

    @property
    def score(self) -> float:
        """Compatibility property returning rrf_score."""
        return self.rrf_score


def reciprocal_rank_fusion(
    dense_results: list[VectorSearchResult],
    sparse_results: list[BM25SearchResult],
    k: int = DEFAULT_RRF_K,
    top_k: int = 5,
) -> list[HybridSearchResult]:
    """
    Merges and deduplicates candidate chunks from Dense (Qdrant) and Sparse (BM25) retrievers
    using Reciprocal Rank Fusion:
        Score(d) = sum_{m in {dense, sparse}} 1 / (k + Rank_m(d))
    where Rank is 1-indexed (1st item is rank 1).
    """
    # Track candidate attributes and component ranks
    meta_map: dict[str, dict[str, Any]] = {}
    dense_ranks: dict[str, int] = {}
    sparse_ranks: dict[str, int] = {}
    dense_scores: dict[str, float] = {}
    sparse_scores: dict[str, float] = {}

    # 1. Process Dense Results
    for rank_idx, item in enumerate(dense_results, start=1):
        cid = item.chunk_id
        dense_ranks[cid] = rank_idx
        dense_scores[cid] = item.score
        if cid not in meta_map:
            meta_map[cid] = {
                "chunk_id": cid,
                "document_id": item.document_id,
                "patient_id": item.patient_id,
                "page_number": item.page_number,
                "chunk_index": item.chunk_index,
                "content": item.content,
                "raw_content": item.raw_content,
                "doc_title": item.doc_title,
                "doc_type": item.doc_type,
                "doc_date": item.doc_date,
            }

    # 2. Process Sparse Results
    for rank_idx, s_item in enumerate(sparse_results, start=1):
        cid = s_item.chunk_id
        sparse_ranks[cid] = rank_idx
        sparse_scores[cid] = s_item.score
        if cid not in meta_map:
            meta_map[cid] = {
                "chunk_id": cid,
                "document_id": s_item.document_id,
                "patient_id": s_item.patient_id,
                "page_number": s_item.page_number,
                "chunk_index": s_item.chunk_index,
                "content": s_item.content,
                "raw_content": s_item.raw_content,
                "doc_title": s_item.doc_title,
                "doc_type": s_item.doc_type,
                "doc_date": s_item.doc_date,
            }

    # 3. Calculate RRF scores
    all_chunk_ids = set(dense_ranks.keys()).union(sparse_ranks.keys())
    rrf_scores: list[tuple[str, float]] = []

    for cid in all_chunk_ids:
        score = 0.0
        if cid in dense_ranks:
            score += 1.0 / (k + dense_ranks[cid])
        if cid in sparse_ranks:
            score += 1.0 / (k + sparse_ranks[cid])
        rrf_scores.append((cid, score))

    # Sort candidates by RRF score descending, breaking ties by lowest combined rank
    rrf_scores.sort(
        key=lambda x: (
            x[1],
            -(dense_ranks.get(x[0], 999) + sparse_ranks.get(x[0], 999)),
        ),
        reverse=True,
    )

    # 4. Construct sorted HybridSearchResult list
    hybrid_results: list[HybridSearchResult] = []
    for cid, rrf_score in rrf_scores[:top_k]:
        meta = meta_map[cid]
        hybrid_results.append(
            HybridSearchResult(
                chunk_id=cid,
                document_id=meta["document_id"],
                patient_id=meta["patient_id"],
                page_number=meta["page_number"],
                chunk_index=meta["chunk_index"],
                content=meta["content"],
                raw_content=meta["raw_content"],
                rrf_score=round(rrf_score, 6),
                dense_rank=dense_ranks.get(cid),
                sparse_rank=sparse_ranks.get(cid),
                dense_score=dense_scores.get(cid),
                sparse_score=sparse_scores.get(cid),
                doc_title=meta["doc_title"],
                doc_type=meta["doc_type"],
                doc_date=meta["doc_date"],
            )
        )

    return hybrid_results
