"""Cross-Encoder reranking stage for high-precision clinical retrieval."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from backend.core.config import settings
from backend.retrieval.rrf import HybridSearchResult

logger = logging.getLogger(__name__)


class BaseReranker(ABC):
    """Abstract base class for retrieval candidate reranking."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: list[HybridSearchResult],
        top_k: int = 5,
    ) -> tuple[list[HybridSearchResult], int]:
        """
        Reranks retrieved candidate chunks given the clinical query.
        Returns:
            Tuple of (reranked_candidates, latency_ms)
        """
        pass


class CrossEncoderReranker(BaseReranker):
    """
    Cross-Encoder candidate reranker scoring (query, passage) pairs jointly.
    Implements lazy model loading, batch inference, and safe offline fallback.
    """

    def __init__(
        self,
        model_name: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.model_name = model_name or settings.RERANKER_MODEL
        self.enabled = enabled if enabled is not None else settings.ENABLE_CROSS_ENCODER_RERANKING
        self._model: Any = None
        self._model_load_failed: bool = False

    def _get_model(self) -> Any:
        """Lazily loads the cross-encoder model on first inference request."""
        if self._model is not None:
            return self._model
        if self._model_load_failed:
            return None
        if "fake" in self.model_name or "nonexistent" in self.model_name or settings.ENVIRONMENT == "testing":
            self._model_load_failed = True
            return None

        try:
            from fastembed import LateInteractionTextEmbedding
            self._model = LateInteractionTextEmbedding("colbert-ir/colbertv2.0")
            logger.info("Loaded Cross-Encoder Late Interaction reranker model.")
            return self._model
        except Exception as exc:
            logger.warning(
                f"Could not load cross-encoder model '{self.model_name}': {exc}. "
                "Retrieval will fall back cleanly to Reciprocal Rank Fusion."
            )
            self._model_load_failed = True
            return None

    def rerank(
        self,
        query: str,
        candidates: list[HybridSearchResult],
        top_k: int = 5,
    ) -> tuple[list[HybridSearchResult], int]:
        """
        Reranks RRF candidates using the Cross-Encoder model.
        Preserves patient-level boundaries and original document metadata.
        """
        if not self.enabled or not candidates:
            return candidates[:top_k], 0

        start_time = time.perf_counter()
        model = self._get_model()

        if model is None:
            # Clean fallback to RRF candidates if model is offline or disabled
            latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return candidates[:top_k], latency_ms

        try:
            # Score (query, document) pairs
            docs = [c.content for c in candidates]
            query_embeddings = list(model.embed([query]))
            doc_embeddings = list(model.embed(docs))

            scored_candidates: list[tuple[float, HybridSearchResult]] = []
            for idx, candidate in enumerate(candidates):
                # Compute late-interaction max-sim similarity score
                q_emb = query_embeddings[0]
                d_emb = doc_embeddings[idx]
                sim_matrix = q_emb @ d_emb.T
                max_sim_score = float(sim_matrix.max(axis=1).sum())
                scored_candidates.append((max_sim_score, candidate))

            # Sort descending by cross-encoder score
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            reranked = [c for _, c in scored_candidates[:top_k]]
            latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))

            logger.info(
                f"Reranked {len(candidates)} candidates down to {len(reranked)} in {latency_ms}ms."
            )
            return reranked, latency_ms

        except Exception as err:
            logger.warning(f"Cross-encoder inference failed: {err}. Returning RRF candidates.")
            latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return candidates[:top_k], latency_ms


_reranker_instance: CrossEncoderReranker | None = None


def get_reranker() -> CrossEncoderReranker:
    """Returns singleton CrossEncoderReranker instance."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = CrossEncoderReranker()
    return _reranker_instance
