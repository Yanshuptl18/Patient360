"""Medical Research Intelligence package for Patient360."""

from backend.research.extractor import StudyParameterExtractor
from backend.research.matrix import (
    build_comparison_matrix,
    determine_evidence_strength,
    export_markdown_dossier,
)
from backend.research.service import ResearchService, get_research_service

__all__ = [
    "StudyParameterExtractor",
    "determine_evidence_strength",
    "build_comparison_matrix",
    "export_markdown_dossier",
    "ResearchService",
    "get_research_service",
]
