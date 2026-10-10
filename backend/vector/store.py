"""Qdrant vector store adapter with collection management, payload indexing, and isolated search."""

import logging
from dataclasses import dataclass
from typing import Any, ClassVar

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    HnswConfigDiff,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from backend.core.config import settings
from backend.core.exceptions import Patient360Exception
from backend.models.chunk import DocumentChunk
from backend.vector.embeddings import FastEmbedProvider, get_embedding_provider

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """Retrieved document chunk with cosine similarity score and metadata."""

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


class QdrantVectorStore:
    """
    Qdrant vector store adapter managing collection lifecycles, HNSW index parameters,
    isolated patient payload filtering, and dense semantic retrieval.
    """

    _instance: ClassVar["QdrantVectorStore | None"] = None

    def __init__(
        self,
        client: QdrantClient | None = None,
        embedder: FastEmbedProvider | None = None,
        collection_name: str | None = None,
    ) -> None:
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.embedder = embedder or get_embedding_provider()

        if client is not None:
            self.client = client
            self.is_embedded = "local" in str(type(getattr(client, "_client", None))).lower()
        elif settings.ENVIRONMENT == "testing":
            logger.info("Using embedded in-memory Qdrant instance for test execution.")
            self.client = QdrantClient(":memory:")
            self.is_embedded = True
        else:
            try:
                # Attempt connection to configured Qdrant service
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    timeout=2,
                )
                # Verify liveness
                self.client.get_collections()
                self.is_embedded = False
                logger.info(f"Connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            except Exception as err:
                logger.warning(
                    f"Could not connect to Qdrant daemon ({err}). Falling back to in-memory embedded vector store."
                )
                self.client = QdrantClient(":memory:")
                self.is_embedded = True

        self.ensure_collection()

    @classmethod
    def get_instance(cls) -> "QdrantVectorStore":
        """Singleton accessor for vector store."""
        if cls._instance is None:
            cls._instance = QdrantVectorStore()
        return cls._instance

    def ensure_collection(self) -> None:
        """
        Ensures the vector collection exists with 384-dim Cosine metrics and HNSW index parameters.
        Creates payload indexes for patient_id and document_id.
        """
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                logger.info(
                    f"Creating Qdrant collection '{self.collection_name}' "
                    f"(dim={self.embedder.dimensions}, distance=Cosine, m=16, ef_construct=100)"
                )
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedder.dimensions,
                        distance=Distance.COSINE,
                    ),
                    hnsw_config=HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                    ),
                )

                # Create payload indexes for fast filtered lookups (server mode only)
                if not self.is_embedded:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="patient_id",
                        field_schema=PayloadSchemaType.KEYWORD,
                    )
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="document_id",
                        field_schema=PayloadSchemaType.KEYWORD,
                    )
        except Exception as err:
            logger.error(f"Error ensuring Qdrant collection: {err}")
            raise Patient360Exception(
                message=f"Failed to initialize vector collection: {err}",
                code="VECTOR_STORE_INIT_FAILED",
                status_code=500,
            ) from err

    def upsert_chunks(self, chunks: list[DocumentChunk]) -> int:
        """
        Encodes document chunks with FastEmbed and upserts them into Qdrant with payload metadata.
        Returns the number of points upserted.
        """
        if not chunks:
            return 0

        texts = [c.content for c in chunks]
        vectors = self.embedder.embed_documents(texts)

        points: list[PointStruct] = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            meta = chunk.metadata_json or {}
            payload: dict[str, Any] = {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "patient_id": meta.get("patient_id"),
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "raw_content": chunk.raw_content,
                "token_count": chunk.token_count,
                "doc_title": meta.get("doc_title", "Untitled"),
                "doc_type": meta.get("doc_type", "patient_record"),
                "doc_date": meta.get("doc_date"),
            }
            points.append(PointStruct(id=chunk.id, vector=vector, payload=payload))

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Upserted {len(points)} vector chunks into '{self.collection_name}'.")
        return len(points)

    def search(
        self,
        query: str,
        patient_id: str | None = None,
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> list[VectorSearchResult]:
        """
        Performs dense semantic similarity search with strict patient payload isolation.
        """
        if not query.strip():
            return []

        query_vector = self.embedder.embed_query(query)

        # Enforce server-side patient payload filter if provided
        query_filter: Filter | None = None
        if patient_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="patient_id",
                        match=MatchValue(value=patient_id),
                    )
                ]
            )

        query_response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold if score_threshold > 0 else None,
        )

        results: list[VectorSearchResult] = []
        for hit in query_response.points:
            payload = hit.payload or {}
            results.append(
                VectorSearchResult(
                    chunk_id=str(hit.id),
                    document_id=payload.get("document_id", ""),
                    patient_id=payload.get("patient_id"),
                    page_number=payload.get("page_number", 1),
                    chunk_index=payload.get("chunk_index", 0),
                    content=payload.get("content", ""),
                    raw_content=payload.get("raw_content", ""),
                    score=float(hit.score),
                    doc_title=payload.get("doc_title", "Untitled"),
                    doc_type=payload.get("doc_type", "patient_record"),
                    doc_date=payload.get("doc_date"),
                )
            )

        return results

    def delete_document_chunks(self, document_id: str) -> None:
        """Removes all vector embeddings belonging to a specific document."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )
        logger.info(f"Deleted vector chunks for document '{document_id}' from '{self.collection_name}'.")

    def delete_patient_chunks(self, patient_id: str) -> None:
        """Removes all vector embeddings belonging to a specific patient dossier."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="patient_id",
                        match=MatchValue(value=patient_id),
                    )
                ]
            ),
        )
        logger.info(f"Deleted vector chunks for patient '{patient_id}' from '{self.collection_name}'.")

    def get_collection_stats(self) -> dict[str, Any]:
        """Returns statistics on the vector store collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "status": "UP",
                "vectors_count": info.points_count or 0,
                "indexed_vectors_count": info.indexed_vectors_count or 0,
                "dimensions": self.embedder.dimensions,
                "is_embedded": self.is_embedded,
            }
        except (UnexpectedResponse, Exception) as err:
            logger.warning(f"Failed to get collection stats: {err}")
            return {
                "collection_name": self.collection_name,
                "status": "DOWN",
                "error": str(err),
            }


def get_vector_store() -> QdrantVectorStore:
    """Dependency helper returning singleton vector store instance."""
    return QdrantVectorStore.get_instance()
