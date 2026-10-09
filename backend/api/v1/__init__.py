"""API v1 router registry."""

from fastapi import APIRouter

from backend.api.v1 import auth, documents, health, patients, vector

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["System Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patient Records"])
api_router.include_router(documents.router, prefix="/documents", tags=["Document Management"])
api_router.include_router(vector.router, prefix="/vector", tags=["Vector Store & Retrieval"])
