"""FastEmbed CPU-optimized dense vector embeddings provider with resilient offline fallback."""

import hashlib
import logging
import math
from typing import ClassVar

from backend.core.config import settings

logger = logging.getLogger(__name__)


class FastEmbedProvider:
    """
    CPU-optimized local embedding provider using FastEmbed and ONNX Runtime.
    Encodes text into 384-dimensional dense vectors using BAAI/bge-small-en-v1.5.
    Includes a deterministic normalized fallback if remote model download is rate-limited.
    """

    _instance: ClassVar["FastEmbedProvider | None"] = None

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        self._embedder = None
        self._init_attempted = False

    def _ensure_embedder(self) -> None:
        if self._init_attempted:
            return
        self._init_attempted = True
        try:
            logger.info(f"Initializing FastEmbed model: {self.model_name} on CPU")
            from fastembed import TextEmbedding

            self._embedder = TextEmbedding(model_name=self.model_name)
            logger.info("FastEmbed model initialized successfully.")
        except Exception as err:
            logger.warning(
                f"FastEmbed remote model initialization unavailable ({err}). "
                "Engaging resilient deterministic dense vector embedding."
            )
            self._embedder = None

    @classmethod
    def get_instance(cls) -> "FastEmbedProvider":
        """Singleton accessor for FastEmbed model."""
        if cls._instance is None:
            cls._instance = FastEmbedProvider()
        return cls._instance

    def _deterministic_embed(self, text: str) -> list[float]:
        """Generates a reproducible 384-dimensional unit vector using n-gram hash projection."""
        vec = [0.0] * self.dimensions
        if not text or not text.strip():
            return vec
        tokens = text.lower().split()
        for token in tokens:
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:16], 16)
            idx = h % self.dimensions
            val = ((h >> 8) % 1000) / 500.0 - 1.0
            vec[idx] += val
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_query(self, query: str) -> list[float]:
        """Encodes a single user search query into a 384-dimensional vector."""
        if not query.strip():
            return [0.0] * self.dimensions
        self._ensure_embedder()
        if self._embedder is not None:
            try:
                vectors = list(self._embedder.embed([query]))
                return [float(x) for x in vectors[0].tolist()]
            except Exception as exc:
                logger.warning(f"FastEmbed query embedding error ({exc}), using deterministic embedding.")
        return self._deterministic_embed(query)

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Encodes a batch of document texts into 384-dimensional dense vectors."""
        if not documents:
            return []
        self._ensure_embedder()
        if self._embedder is not None:
            try:
                cleaned_docs = [doc if doc.strip() else "empty document" for doc in documents]
                vectors = list(self._embedder.embed(cleaned_docs))
                return [v.tolist() for v in vectors]
            except Exception as exc:
                logger.warning(f"FastEmbed document embedding error ({exc}), using deterministic embedding.")
        return [self._deterministic_embed(doc) for doc in documents]


def get_embedding_provider() -> FastEmbedProvider:
    """Dependency injection helper returning singleton FastEmbedProvider."""
    return FastEmbedProvider.get_instance()
