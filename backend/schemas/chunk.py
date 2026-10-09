"""Pydantic schemas for document chunks and ingestion responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ChunkResponse(BaseModel):
    """Metadata and content for a single extracted document chunk."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    chunk_index: int
    page_number: int
    content: str
    raw_content: str
    token_count: int
    metadata_json: dict[str, Any]
    created_at: datetime


class IngestionResponse(BaseModel):
    """Summary response returned when document ingestion is triggered or completed."""

    document_id: str
    status: str
    chunk_count: int
    total_tokens: int
    pages_processed: int
    message: str
