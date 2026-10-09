"""Vector search and Qdrant collection status API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db
from backend.core.exceptions import AuthorizationError
from backend.models.user import User
from backend.patients.service import check_user_patient_access
from backend.schemas.vector import (
    VectorSearchRequest,
    VectorSearchResultItem,
    VectorStatsResponse,
)
from backend.vector.store import get_vector_store

router = APIRouter()


@router.get("/stats", response_model=VectorStatsResponse)
def get_vector_collection_statistics(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> VectorStatsResponse:
    """Returns Qdrant vector collection health, dimensions, and indexed point counts."""
    store = get_vector_store()
    stats = store.get_collection_stats()
    return VectorStatsResponse(
        collection_name=stats.get("collection_name", "patient360_chunks"),
        status=stats.get("status", "UP"),
        vectors_count=stats.get("vectors_count", 0),
        indexed_vectors_count=stats.get("indexed_vectors_count", 0),
        dimensions=stats.get("dimensions", 384),
        is_embedded=stats.get("is_embedded", False),
    )


@router.post("/search", response_model=list[VectorSearchResultItem], status_code=status.HTTP_200_OK)
def search_vector_embeddings(
    request: VectorSearchRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[VectorSearchResultItem]:
    """
    Executes dense semantic similarity search over document chunks.
    Enforces strict patient-level access boundaries if patient_id is specified.
    """
    if request.patient_id:
        # Enforce server-side patient isolation
        if not check_user_patient_access(db, user=current_user, patient_id=request.patient_id, min_permission="read"):
            raise AuthorizationError(
                f"User '{current_user.email}' is not authorized to search patient dossier '{request.patient_id}'."
            )

    store = get_vector_store()
    results = store.search(
        query=request.query,
        patient_id=request.patient_id,
        top_k=request.top_k,
        score_threshold=request.score_threshold,
    )

    return [
        VectorSearchResultItem(
            chunk_id=r.chunk_id,
            document_id=r.document_id,
            patient_id=r.patient_id,
            page_number=r.page_number,
            chunk_index=r.chunk_index,
            content=r.content,
            raw_content=r.raw_content,
            score=round(r.score, 4),
            doc_title=r.doc_title,
            doc_type=r.doc_type,
            doc_date=r.doc_date,
        )
        for r in results
    ]
