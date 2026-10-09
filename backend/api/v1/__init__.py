"""API v1 router registry."""

from fastapi import APIRouter

from backend.api.v1 import auth, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["System Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
