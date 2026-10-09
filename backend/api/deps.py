"""Reusable FastAPI dependency providers."""

from backend.core.database import get_db

# Re-export get_db for easy consumption in route handlers
__all__ = ["get_db"]
