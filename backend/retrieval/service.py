"""Hybrid retrieval service orchestrating dense vector search, sparse BM25, and RRF."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models.chunk import DocumentChunk
from backend.models.document import Document
from backend.retrieval.bm25 import (
    BM25Document,
    PatientBM25Registry,
    get_bm25_registry,
)
from backend.retrieval.reranker import CrossEncoderReranker, get_reranker
from backend.retrieval.rrf import (
    DEFAULT_RRF_K,
    HybridSearchResult,
    reciprocal_rank_fusion,
)
from backend.vector.store import QdrantVectorStore, get_vector_store

logger = logging.getLogger(__name__)


class HybridRetrievalService:
    """Combines Qdrant dense vector search, sparse BM25, and optional Cross-Encoder reranking."""

    def __init__(
        self,
        vector_store: QdrantVectorStore | None = None,
        bm25_registry: PatientBM25Registry | None = None,
        reranker: CrossEncoderReranker | None = None,
    ) -> None:
        self.vector_store = vector_store or get_vector_store()
        self.bm25_registry = bm25_registry or get_bm25_registry()
        self.reranker = reranker or get_reranker()

    def sync_patient_bm25_from_db(self, db: Session, patient_id: str) -> None:
        """Hydrates or warms up the in-memory BM25 index from persistent database chunks."""
        chunks = (
            db.query(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(Document.patient_id == patient_id)
            .all()
        )
        if not chunks:
            return

        bm25_docs = [
            BM25Document(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                patient_id=patient_id,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                raw_content=chunk.raw_content,
                doc_title=doc.title,
                doc_type=doc.doc_type,
                doc_date=str(doc.doc_date) if doc.doc_date else None,
            )
            for chunk, doc in chunks
        ]
        self.bm25_registry.get_index_for_patient(patient_id).index_documents(bm25_docs)
        logger.info(
            f"Warmed in-memory BM25 index for patient '{patient_id}' with {len(bm25_docs)} chunks."
        )

    def search(
        self,
        query: str,
        patient_id: str,
        top_k: int = 5,
        dense_candidates_k: int = 20,
        sparse_candidates_k: int = 20,
        rrf_k: int = DEFAULT_RRF_K,
        db: Session | None = None,
    ) -> tuple[list[HybridSearchResult], dict[str, Any]]:
        """
        Executes hybrid retrieval:
        1. Dense retrieval via Qdrant (top 20)
        2. Sparse retrieval via BM25 (top 20)
        3. Reciprocal Rank Fusion merge (top K)
        Returns:
            Tuple of (list[HybridSearchResult], metadata_dict)
        """
        # Ensure BM25 index is populated if DB session is available
        bm25_index = self.bm25_registry.get_index_for_patient(patient_id)
        if bm25_index.total_docs == 0 and db is not None:
            self.sync_patient_bm25_from_db(db, patient_id)

        # 1. Dense retrieval
        dense_results = self.vector_store.search(
            query=query,
            patient_id=patient_id,
            top_k=dense_candidates_k,
        )

        # 2. Sparse retrieval
        sparse_results = bm25_index.search(
            query=query,
            top_k=sparse_candidates_k,
        )

        # 3. Reciprocal Rank Fusion
        enable_rerank = self.reranker.enabled
        rrf_top_k = settings.RERANKER_TOP_N if enable_rerank else top_k

        hybrid_results = reciprocal_rank_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            k=rrf_k,
            top_k=rrf_top_k,
        )

        rerank_latency_ms = 0
        rerank_applied = False
        final_results = hybrid_results

        # 4. Optional Cross-Encoder Reranking
        if enable_rerank and hybrid_results:
            final_results, rerank_latency_ms = self.reranker.rerank(
                query=query,
                candidates=hybrid_results,
                top_k=top_k,
            )
            rerank_applied = True
        else:
            final_results = hybrid_results[:top_k]

        metadata = {
            "dense_candidates_count": len(dense_results),
            "sparse_candidates_count": len(sparse_results),
            "merged_candidates_count": len(final_results),
            "rrf_k": rrf_k,
            "rerank_applied": rerank_applied,
            "rerank_latency_ms": rerank_latency_ms,
        }

        return final_results, metadata


_retrieval_service: HybridRetrievalService | None = None


def get_hybrid_retrieval_service() -> HybridRetrievalService:
    """Returns singleton HybridRetrievalService instance."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = HybridRetrievalService()
    return _retrieval_service
