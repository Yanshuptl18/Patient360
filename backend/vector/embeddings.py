"""FastEmbed CPU-optimized dense vector embeddings provider."""

import logging
from typing import ClassVar

from fastembed import TextEmbedding

from backend.core.config import settings

logger = logging.getLogger(__name__)


class FastEmbedProvider:
    """
    CPU-optimized local embedding provider using FastEmbed and ONNX Runtime.
    Encodes text into 384-dimensional dense vectors using BAAI/bge-small-en-v1.5.
    """

    _instance: ClassVar["FastEmbedProvider | None"] = None

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        logger.info(f"Initializing FastEmbed model: {self.model_name} on CPU")
        self._embedder = TextEmbedding(model_name=self.model_name)
        self.dimensions = settings.EMBEDDING_DIMENSIONS

    @classmethod
    def get_instance(cls) -> "FastEmbedProvider":
        """Singleton accessor for FastEmbed model."""
        if cls._instance is None:
            cls._instance = FastEmbedProvider()
        return cls._instance

    def embed_query(self, query: str) -> list[float]:
        """Encodes a single user search query into a 384-dimensional vector."""
        if not query.strip():
            return [0.0] * self.dimensions
        # BGE models benefit from query formatting or standard encoding
        vectors = list(self._embedder.embed([query]))
        return [float(x) for x in vectors[0].tolist()]

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Encodes a batch of document texts into 384-dimensional dense vectors."""
        if not documents:
            return []
        cleaned_docs = [doc if doc.strip() else "empty document" for doc in documents]
        vectors = list(self._embedder.embed(cleaned_docs))
        return [v.tolist() for v in vectors]


def get_embedding_provider() -> FastEmbedProvider:
    """Dependency injection helper returning singleton FastEmbedProvider."""
    return FastEmbedProvider.get_instance()
