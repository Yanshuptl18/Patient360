"""Unit tests for Reciprocal Rank Fusion (RRF) mathematical ranking and candidate merging."""

import pytest

from backend.retrieval.bm25 import BM25SearchResult
from backend.retrieval.rrf import reciprocal_rank_fusion
from backend.vector.store import VectorSearchResult


def test_reciprocal_rank_fusion_mathematical_scoring() -> None:
    """Verifies that RRF scores follow 1 / (k + rank) and prioritize dual-ranked candidates."""
    # Chunk 1 is ranked #1 in both Dense and Sparse
    # Chunk 2 is ranked #2 in Dense and #1 in Sparse
    # Chunk 3 is only in Sparse (rank #3)
    # Chunk 4 is only in Dense (rank #3)

    dense_list = [
        VectorSearchResult(
            chunk_id="chunk-dual-top",
            document_id="doc-1",
            patient_id="pat-1",
            page_number=1,
            chunk_index=0,
            content="Dual top match content",
            raw_content="Dual top match content",
            score=0.95,
            doc_title="Doc1.pdf",
            doc_type="lab_report",
            doc_date="2024-01-01",
        ),
        VectorSearchResult(
            chunk_id="chunk-dense-second",
            document_id="doc-2",
            patient_id="pat-1",
            page_number=2,
            chunk_index=1,
            content="Dense second match content",
            raw_content="Dense second match content",
            score=0.88,
            doc_title="Doc2.pdf",
            doc_type="patient_record",
            doc_date="2024-01-02",
        ),
        VectorSearchResult(
            chunk_id="chunk-dense-only",
            document_id="doc-3",
            patient_id="pat-1",
            page_number=3,
            chunk_index=2,
            content="Dense only match content",
            raw_content="Dense only match content",
            score=0.81,
            doc_title="Doc3.pdf",
            doc_type="patient_record",
            doc_date="2024-01-03",
        ),
    ]

    sparse_list = [
        BM25SearchResult(
            chunk_id="chunk-dual-top",
            document_id="doc-1",
            patient_id="pat-1",
            page_number=1,
            chunk_index=0,
            content="Dual top match content",
            raw_content="Dual top match content",
            score=12.5,
            doc_title="Doc1.pdf",
            doc_type="lab_report",
            doc_date="2024-01-01",
        ),
        BM25SearchResult(
            chunk_id="chunk-dense-second",
            document_id="doc-2",
            patient_id="pat-1",
            page_number=2,
            chunk_index=1,
            content="Dense second match content",
            raw_content="Dense second match content",
            score=9.8,
            doc_title="Doc2.pdf",
            doc_type="patient_record",
            doc_date="2024-01-02",
        ),
        BM25SearchResult(
            chunk_id="chunk-sparse-only",
            document_id="doc-4",
            patient_id="pat-1",
            page_number=1,
            chunk_index=3,
            content="Sparse only match content",
            raw_content="Sparse only match content",
            score=7.4,
            doc_title="Doc4.pdf",
            doc_type="lab_report",
            doc_date="2024-01-04",
        ),
    ]

    # Standard RRF with k=60
    results = reciprocal_rank_fusion(dense_results=dense_list, sparse_results=sparse_list, k=60, top_k=5)

    assert len(results) == 4

    # 1st candidate: rank 1 dense + rank 1 sparse
    expected_top_score = (1.0 / 61) + (1.0 / 61)  # ~0.032787
    assert results[0].chunk_id == "chunk-dual-top"
    assert results[0].rrf_score == pytest.approx(expected_top_score, rel=1e-3)
    assert results[0].dense_rank == 1
    assert results[0].sparse_rank == 1
    assert results[0].dense_score == 0.95
    assert results[0].sparse_score == 12.5

    # 2nd candidate: rank 2 dense + rank 2 sparse
    expected_second_score = (1.0 / 62) + (1.0 / 62)  # ~0.032258
    assert results[1].chunk_id == "chunk-dense-second"
    assert results[1].rrf_score == pytest.approx(expected_second_score, rel=1e-3)
    assert results[1].dense_rank == 2
    assert results[1].sparse_rank == 2

    # Single-modality candidates follow
    single_cids = {results[2].chunk_id, results[3].chunk_id}
    assert "chunk-dense-only" in single_cids
    assert "chunk-sparse-only" in single_cids
