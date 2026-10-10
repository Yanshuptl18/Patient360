"""Grounded Retrieval-Augmented Generation (RAG) and evidence synthesis engine."""

from backend.rag.citations import CitationVerifier
from backend.rag.llm import BaseLLMProvider, get_llm_provider
from backend.rag.prompt import GroundedPromptBuilder
from backend.rag.service import RAGService, get_rag_service

__all__ = [
    "BaseLLMProvider",
    "get_llm_provider",
    "GroundedPromptBuilder",
    "CitationVerifier",
    "RAGService",
    "get_rag_service",
]
