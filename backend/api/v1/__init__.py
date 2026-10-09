"""API v1 router registry."""

from fastapi import APIRouter

from backend.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["System Health"])
