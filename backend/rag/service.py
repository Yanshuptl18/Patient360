"""End-to-end Grounded RAG orchestrator integrating retrieval, prompt assembly, and verification."""

import logging
import time

from sqlalchemy.orm import Session

from backend.rag.citations import ABSTENTION_PHRASES, CitationVerifier
from backend.rag.llm import BaseLLMProvider, get_llm_provider
from backend.rag.prompt import GroundedPromptBuilder
from backend.rag.safety import (
    apply_clinical_safety_disclaimer,
    check_emergency_symptoms,
    detect_prompt_injection,
    sanitize_prompt_input,
)
from backend.retrieval.service import (
    HybridRetrievalService,
    get_hybrid_retrieval_service,
)
from backend.schemas.rag import RAGQueryResponse, RetrievalMetadata

logger = logging.getLogger(__name__)


class RAGService:
    """Orchestrates grounded question-answering workflows across patient dossiers."""

    def __init__(
        self,
        retrieval_service: HybridRetrievalService | None = None,
        llm_provider: BaseLLMProvider | None = None,
        prompt_builder: GroundedPromptBuilder | None = None,
        citation_verifier: CitationVerifier | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service or get_hybrid_retrieval_service()
        self.llm_provider = llm_provider or get_llm_provider()
        self.prompt_builder = prompt_builder or GroundedPromptBuilder()
        self.citation_verifier = citation_verifier or CitationVerifier()

    def query(
        self,
        query: str,
        patient_id: str,
        top_k: int = 5,
        db: Session | None = None,
    ) -> RAGQueryResponse:
        """
        Executes hybrid retrieval (Dense + BM25 + RRF) against patient dossier, constructs
        evidence-grounded prompt, generates answer, and parses/verifies citations.
        Enforces responsible AI safety filters, prompt sanitization, and clinical disclaimers.
        """
        start_total = time.perf_counter()

        # 0. Safety review: emergency escalation & prompt injection detection
        is_emergency, emergency_cat = check_emergency_symptoms(query)
        is_injection, _ = detect_prompt_injection(query)
        effective_query = sanitize_prompt_input(query) if is_injection else query

        # 1. Hybrid candidate retrieval (Dense + Sparse + RRF)
        start_retrieval = time.perf_counter()
        retrieved_chunks, ret_meta = self.retrieval_service.search(
            query=effective_query,
            patient_id=patient_id,
            top_k=top_k,
            db=db,
        )
        retrieval_latency_ms = max(1, int((time.perf_counter() - start_retrieval) * 1000))

        # Handle zero retrieved evidence
        if not retrieved_chunks:
            total_latency_ms = max(1, int((time.perf_counter() - start_total) * 1000))
            raw_abstention = ABSTENTION_PHRASES[0].capitalize() + "."
            safe_abstention = apply_clinical_safety_disclaimer(
                raw_abstention,
                is_emergency=is_emergency,
                emergency_category=emergency_cat,
            )
            limitations = ["No relevant clinical documents found for this patient."]
            if is_emergency and emergency_cat:
                limitations.insert(0, f"EMERGENCY RED-FLAG: {emergency_cat}. Recommend immediate clinical triage.")
            if is_injection:
                limitations.append("Adversarial prompt injection pattern detected and neutralized.")

            return RAGQueryResponse(
                query=query,
                patient_id=patient_id,
                answer=safe_abstention,
                citations=[],
                limitations=limitations,
                confidence_score=0.0,
                retrieval_metadata=RetrievalMetadata(
                    dense_candidates_count=ret_meta.get("dense_candidates_count", 0),
                    sparse_candidates_count=ret_meta.get("sparse_candidates_count", 0),
                    merged_candidates_count=0,
                    retrieval_latency_ms=retrieval_latency_ms,
                    generation_latency_ms=0,
                    total_latency_ms=total_latency_ms,
                    is_abstention=True,
                ),
            )

        # 2. Build structured grounded prompt
        prompt = self.prompt_builder.build_prompt(
            query=effective_query,
            retrieved_chunks=retrieved_chunks,
        )

        # 3. LLM Generation
        start_generation = time.perf_counter()
        llm_response = self.llm_provider.generate_answer(
            prompt=prompt,
            system_prompt=self.prompt_builder.system_prompt,
            temperature=0.0,
        )
        generation_latency_ms = max(1, int((time.perf_counter() - start_generation) * 1000))

        # 4. Citation Parsing & Claim Verification
        citations, is_abstention = self.citation_verifier.verify(
            answer=llm_response.content,
            retrieved_chunks=retrieved_chunks,
        )

        # 5. Derive limitations and confidence score
        limitations = []
        if is_abstention:
            confidence_score = 0.0
            limitations.append("The available records do not contain direct evidence addressing this inquiry.")
        else:
            supported_count = sum(1 for c in citations if c.verification_status == "supported")
            unsupported_count = sum(1 for c in citations if c.verification_status == "unsupported")

            if unsupported_count > 0:
                limitations.append(
                    f"{unsupported_count} citation(s) could not be definitively matched to retrieved passages."
                )

            if citations:
                support_ratio = supported_count / len(citations)
                avg_chunk_score = sum(c.score for c in retrieved_chunks) / len(retrieved_chunks)
                confidence_score = round(min(1.0, max(0.1, (support_ratio * 0.7) + (avg_chunk_score * 0.3))), 2)
            else:
                confidence_score = 0.5
                limitations.append("Response lacks explicit citation tags; verify manually against source files.")

        if is_emergency and emergency_cat:
            limitations.insert(0, f"EMERGENCY RED-FLAG: {emergency_cat}. Recommend immediate clinical triage.")
        if is_injection:
            limitations.append("Adversarial prompt injection pattern detected and neutralized.")

        # 6. Apply Responsible AI safety disclaimer & emergency notice
        safe_answer = apply_clinical_safety_disclaimer(
            answer=llm_response.content,
            is_emergency=is_emergency,
            emergency_category=emergency_cat,
        )

        total_latency_ms = max(1, int((time.perf_counter() - start_total) * 1000))

        return RAGQueryResponse(
            query=query,
            patient_id=patient_id,
            answer=safe_answer,
            citations=citations,
            limitations=limitations,
            confidence_score=confidence_score,
            retrieval_metadata=RetrievalMetadata(
                dense_candidates_count=ret_meta.get("dense_candidates_count", len(retrieved_chunks)),
                sparse_candidates_count=ret_meta.get("sparse_candidates_count", 0),
                merged_candidates_count=len(retrieved_chunks),
                retrieval_latency_ms=retrieval_latency_ms,
                generation_latency_ms=generation_latency_ms,
                total_latency_ms=total_latency_ms,
                is_abstention=is_abstention,
            ),
        )


_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """Returns singleton RAGService instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
