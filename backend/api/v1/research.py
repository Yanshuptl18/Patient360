"""Medical Research Intelligence API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.research.service import ResearchService, get_research_service
from backend.schemas.research import (
    DossierExportRequest,
    DossierExportResponse,
    ResearchStudyResponse,
    StudyCompareRequest,
    StudyComparisonMatrix,
)

router = APIRouter()


@router.post(
    "/extract/{document_id}",
    response_model=ResearchStudyResponse,
    status_code=status.HTTP_200_OK,
)
def extract_research_study(
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResearchService, Depends(get_research_service)],
) -> ResearchStudyResponse:
    """
    Extracts study methodology parameters (DOI, PMID, design, sample size, endpoints) from document.
    """
    study = service.extract_study_from_document(
        db=db,
        document_id=document_id,
        force_reextract=True,
        user_id=current_user.id,
    )
    return ResearchStudyResponse.model_validate(study)


@router.get(
    "/studies",
    response_model=list[ResearchStudyResponse],
    status_code=status.HTTP_200_OK,
)
def list_research_studies(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResearchService, Depends(get_research_service)],
    search: Annotated[str | None, Query()] = None,
    study_design: Annotated[str | None, Query()] = None,
) -> list[ResearchStudyResponse]:
    """Retrieves all indexed biomedical research studies and clinical guidelines."""
    studies = service.list_studies(db=db, search=search, study_design=study_design)
    return [ResearchStudyResponse.model_validate(s) for s in studies]


@router.get(
    "/studies/{study_id}",
    response_model=ResearchStudyResponse,
    status_code=status.HTTP_200_OK,
)
def get_research_study(
    study_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResearchService, Depends(get_research_service)],
) -> ResearchStudyResponse:
    """Retrieves metadata and methodology parameters for an individual research study."""
    study = service.get_study(db=db, study_id=study_id)
    return ResearchStudyResponse.model_validate(study)


@router.post(
    "/compare",
    response_model=StudyComparisonMatrix,
    status_code=status.HTTP_200_OK,
)
def compare_research_studies(
    payload: StudyCompareRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResearchService, Depends(get_research_service)],
) -> StudyComparisonMatrix:
    """
    Constructs a structured Evidence Comparison Matrix contrasting multiple research studies side-by-side.
    """
    return service.compare_studies(
        db=db,
        study_ids=payload.study_ids,
        comparison_topic=payload.comparison_topic,
        user_id=current_user.id,
    )


@router.post(
    "/export",
    response_model=DossierExportResponse,
    status_code=status.HTTP_200_OK,
)
def export_research_dossier(
    payload: DossierExportRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResearchService, Depends(get_research_service)],
) -> DossierExportResponse:
    """
    Generates and exports a cited research synthesis dossier in standardized Markdown format.
    """
    return service.export_dossier(
        db=db,
        study_ids=payload.study_ids,
        comparison_topic=payload.comparison_topic,
        title=payload.title,
        user_id=current_user.id,
    )
