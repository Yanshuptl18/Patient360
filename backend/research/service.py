"""Research intelligence service orchestrating study extraction, comparative matrices, and dossier exports."""

import datetime
import logging

from sqlalchemy.orm import Session

from backend.audit.service import log_audit_event
from backend.core.exceptions import EntityNotFoundError
from backend.models.chunk import DocumentChunk
from backend.models.document import Document
from backend.models.research import ResearchStudy
from backend.research.extractor import StudyParameterExtractor
from backend.research.matrix import build_comparison_matrix, export_markdown_dossier
from backend.schemas.research import (
    DossierExportResponse,
    StudyComparisonMatrix,
)

logger = logging.getLogger(__name__)


class ResearchService:
    """Service handling biomedical publication analysis, comparative study matrices, and dossier exports."""

    def __init__(self) -> None:
        self.extractor = StudyParameterExtractor()

    def extract_study_from_document(
        self,
        db: Session,
        document_id: str,
        force_reextract: bool = False,
        user_id: str | None = None,
    ) -> ResearchStudy:
        """
        Extracts study parameters and trial methodologies from document chunks.
        Idempotent: updates existing ResearchStudy record if force_reextract is True.
        """
        doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted.is_(False)).first()
        if not doc:
            raise EntityNotFoundError(f"Document with ID '{document_id}' not found.")

        existing = db.query(ResearchStudy).filter(ResearchStudy.document_id == document_id).first()
        if existing and not force_reextract:
            return existing

        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

        full_text = "\n\n".join([c.content for c in chunks]) if chunks else doc.title
        extracted = self.extractor.extract_parameters(
            full_text=full_text,
            document_title=doc.title,
            doc_date=doc.doc_date,
        )

        if existing:
            existing.title = extracted["title"]
            existing.doi = extracted["doi"]
            existing.pmid = extracted["pmid"]
            existing.authors = extracted["authors"]
            existing.publication_date = extracted["publication_date"]
            existing.study_design = extracted["study_design"]
            existing.sample_size = extracted["sample_size"]
            existing.population_description = extracted["population_description"]
            existing.intervention = extracted["intervention"]
            existing.primary_outcome = extracted["primary_outcome"]
            existing.limitations = extracted["limitations"]
            study = existing
        else:
            study = ResearchStudy(
                document_id=document_id,
                title=extracted["title"],
                doi=extracted["doi"],
                pmid=extracted["pmid"],
                authors=extracted["authors"],
                publication_date=extracted["publication_date"],
                study_design=extracted["study_design"],
                sample_size=extracted["sample_size"],
                population_description=extracted["population_description"],
                intervention=extracted["intervention"],
                primary_outcome=extracted["primary_outcome"],
                limitations=extracted["limitations"],
            )
            db.add(study)

        db.commit()
        db.refresh(study)

        log_audit_event(
            db=db,
            action="RESEARCH_STUDY_EXTRACTED",
            resource_type="research_study",
            user_id=user_id,
            resource_id=study.id,
            details={
                "title": study.title,
                "study_design": study.study_design,
                "sample_size": study.sample_size,
            },
        )

        return study

    def list_studies(
        self,
        db: Session,
        search: str | None = None,
        study_design: str | None = None,
    ) -> list[ResearchStudy]:
        """Lists indexed biomedical research studies with optional filtering."""
        query = db.query(ResearchStudy)
        if study_design and study_design.strip():
            query = query.filter(ResearchStudy.study_design == study_design.strip())
        if search and search.strip():
            s = f"%{search.strip()}%"
            query = query.filter(
                (ResearchStudy.title.ilike(s))
                | (ResearchStudy.doi.ilike(s))
                | (ResearchStudy.pmid.ilike(s))
                | (ResearchStudy.authors.ilike(s))
            )

        return query.order_by(ResearchStudy.created_at.desc()).all()

    def get_study(self, db: Session, study_id: str) -> ResearchStudy:
        """Retrieves a single research study by ID or raises EntityNotFoundError."""
        study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
        if not study:
            raise EntityNotFoundError(f"Research study with ID '{study_id}' not found.")
        return study

    def compare_studies(
        self,
        db: Session,
        study_ids: list[str],
        comparison_topic: str | None = None,
        user_id: str | None = None,
    ) -> StudyComparisonMatrix:
        """Constructs an Evidence Comparison Matrix contrasting the specified studies."""
        studies = db.query(ResearchStudy).filter(ResearchStudy.id.in_(study_ids)).all()
        if not studies:
            raise EntityNotFoundError("None of the specified research studies were found.")

        matrix = build_comparison_matrix(studies=studies, comparison_topic=comparison_topic)

        log_audit_event(
            db=db,
            action="STUDIES_COMPARED",
            resource_type="research_matrix",
            user_id=user_id,
            details={
                "studies_count": len(studies),
                "topic": comparison_topic,
                "study_ids": study_ids,
            },
        )

        return matrix

    def export_dossier(
        self,
        db: Session,
        study_ids: list[str],
        comparison_topic: str | None = None,
        title: str | None = None,
        user_id: str | None = None,
    ) -> DossierExportResponse:
        """Generates and exports an executive evidence dossier in GitHub-flavored Markdown."""
        matrix = self.compare_studies(
            db=db,
            study_ids=study_ids,
            comparison_topic=comparison_topic,
            user_id=user_id,
        )
        dossier_title = title or f"Clinical Evidence Dossier: {matrix.comparison_topic}"
        markdown_text = export_markdown_dossier(matrix=matrix, custom_title=dossier_title)

        log_audit_event(
            db=db,
            action="RESEARCH_DOSSIER_EXPORTED",
            resource_type="research_dossier",
            user_id=user_id,
            details={"studies_count": len(study_ids), "title": dossier_title},
        )

        return DossierExportResponse(
            title=dossier_title,
            markdown_content=markdown_text,
            studies_included_count=matrix.studies_count,
            generated_at_iso=datetime.datetime.now(datetime.UTC).isoformat(),
        )


_research_service: ResearchService | None = None


def get_research_service() -> ResearchService:
    """Singleton accessor for ResearchService."""
    global _research_service
    if _research_service is None:
        _research_service = ResearchService()
    return _research_service
