"""Unit tests and benchmark comparison for Cross-Encoder reranking stage."""

from backend.retrieval.reranker import CrossEncoderReranker
from backend.retrieval.rrf import HybridSearchResult


def make_candidate(chunk_id: str, content: str, score: float) -> HybridSearchResult:
    return HybridSearchResult(
        chunk_id=chunk_id,
        document_id="doc-1",
        patient_id="pat-1",
        page_number=1,
        chunk_index=0,
        content=content,
        raw_content=content,
        rrf_score=score,
        dense_rank=1,
        sparse_rank=1,
        dense_score=0.9,
        sparse_score=10.0,
        doc_title="Clinical Report",
        doc_type="patient_record",
        doc_date="2024-01-01",
    )


def test_reranker_disabled_returns_original_order() -> None:
    """Verifies that when reranking is disabled, candidate order and top_k are preserved."""
    reranker = CrossEncoderReranker(enabled=False)
    candidates = [
        make_candidate("c1", "Patient has diabetes mellitus type 2.", 0.03),
        make_candidate("c2", "Patient denies chest pain.", 0.02),
        make_candidate("c3", "Potassium is normal at 4.0 mEq/L.", 0.01),
    ]

    results, lat = reranker.rerank("What is the potassium level?", candidates, top_k=2)
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert results[1].chunk_id == "c2"
    assert lat == 0


def test_reranker_fallback_on_empty_candidates() -> None:
    """Verifies safe handling of empty candidate lists."""
    reranker = CrossEncoderReranker(enabled=True)
    results, lat = reranker.rerank("Query", [], top_k=5)
    assert results == []
    assert lat == 0


def test_reranker_offline_safe_fallback() -> None:
    """Verifies that if cross-encoder model cannot be downloaded/loaded, original candidates are returned."""
    reranker = CrossEncoderReranker(model_name="nonexistent/fake-model-path", enabled=True)
    candidates = [
        make_candidate("c1", "EGFR mutation exon 21 L858R positive.", 0.05),
        make_candidate("c2", "Vital signs: HR 72, BP 120/80.", 0.04),
    ]

    results, lat = reranker.rerank("What EGFR mutation was detected?", candidates, top_k=2)
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert lat >= 0
