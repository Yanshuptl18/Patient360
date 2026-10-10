"""Pydantic Request and Response Schemas Package."""

from backend.schemas.audit import AuditLogCreate, AuditLogResponse
from backend.schemas.auth import (
    LoginRequest,
    RoleEnum,
    TokenPayload,
    TokenRefreshRequest,
    TokenResponse,
    UserBase,
    UserCreate,
    UserResponse,
)
from backend.schemas.chunk import ChunkResponse, IngestionResponse
from backend.schemas.document import (
    DocTypeEnum,
    DocumentResponse,
    DocumentUploadResponse,
    IngestionStatusEnum,
)
from backend.schemas.patient import (
    PatientBase,
    PatientCreate,
    PatientResponse,
    PermissionGrantRequest,
)
from backend.schemas.rag import (
    CitationItem,
    RAGFeedbackRequest,
    RAGFeedbackResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RetrievalMetadata,
)
from backend.schemas.vector import (
    HybridSearchRequest,
    HybridSearchResultItem,
    VectorSearchRequest,
    VectorSearchResultItem,
    VectorStatsResponse,
)

__all__ = [
    "RoleEnum",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "LoginRequest",
    "TokenResponse",
    "TokenRefreshRequest",
    "TokenPayload",
    "AuditLogCreate",
    "AuditLogResponse",
    "PatientBase",
    "PatientCreate",
    "PatientResponse",
    "PermissionGrantRequest",
    "DocTypeEnum",
    "IngestionStatusEnum",
    "DocumentResponse",
    "DocumentUploadResponse",
    "ChunkResponse",
    "IngestionResponse",
    "VectorSearchRequest",
    "VectorSearchResultItem",
    "VectorStatsResponse",
    "HybridSearchRequest",
    "HybridSearchResultItem",
    "RAGQueryRequest",
    "RAGQueryResponse",
    "CitationItem",
    "RetrievalMetadata",
    "RAGFeedbackRequest",
    "RAGFeedbackResponse",
]
