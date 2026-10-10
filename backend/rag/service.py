"""End-to-end Grounded RAG orchestrator integrating retrieval, prompt assembly, and verification."""

import logging
import time

from backend.rag.citations import ABSTENTION_PHRASES, CitationVerifier
from backend.rag.llm import BaseLLMProvider, get_llm_provider
from backend.rag.prompt import GroundedPromptBuilder
from backend.schemas.rag import RAGQueryResponse, RetrievalMetadata
from backend.vector.store import QdrantVectorStore, get_vector_store

logger = logging.getLogger(__name__)


class RAGService:
    """Orchestrates grounded question-answering workflows across patient dossiers."""

    def __init__(
        self,
        vector_store: QdrantVectorStore | None = None,
        llm_provider: BaseLLMProvider | None = None,
        prompt_builder: GroundedPromptBuilder | None = None,
        citation_verifier: CitationVerifier | None = None,
    ) -> None:
        self.vector_store = vector_store or get_vector_store()
        self.llm_provider = llm_provider or get_llm_provider()
        self.prompt_builder = prompt_builder or GroundedPromptBuilder()
        self.citation_verifier = citation_verifier or CitationVerifier()

    def query(
        self,
        query: str,
        patient_id: str,
        top_k: int = 5,
    ) -> RAGQueryResponse:
        """
        Executes dense retrieval against patient dossier, constructs evidence-grounded prompt,
        generates answer, and parses/verifies citations.
        """
        start_total = time.perf_counter()

        # 1. Dense vector candidate retrieval
        start_retrieval = time.perf_counter()
        retrieved_chunks = self.vector_store.search(
            query=query,
            patient_id=patient_id,
            top_k=top_k,
        )
        retrieval_latency_ms = max(1, int((time.perf_counter() - start_retrieval) * 1000))

        # Handle zero retrieved evidence
        if not retrieved_chunks:
            total_latency_ms = max(1, int((time.perf_counter() - start_total) * 1000))
            return RAGQueryResponse(
                query=query,
                patient_id=patient_id,
                answer=ABSTENTION_PHRASES[0].capitalize() + ".",
                citations=[],
                limitations=["No relevant clinical documents found for this patient."],
                confidence_score=0.0,
                retrieval_metadata=RetrievalMetadata(
                    dense_candidates_count=0,
                    merged_candidates_count=0,
                    retrieval_latency_ms=retrieval_latency_ms,
                    generation_latency_ms=0,
                    total_latency_ms=total_latency_ms,
                    is_abstention=True,
                ),
            )

        # 2. Build structured grounded prompt
        prompt = self.prompt_builder.build_prompt(
            query=query,
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
        limitations: list[str] = []
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

        total_latency_ms = max(1, int((time.perf_counter() - start_total) * 1000))

        return RAGQueryResponse(
            query=query,
            patient_id=patient_id,
            answer=llm_response.content,
            citations=citations,
            limitations=limitations,
            confidence_score=confidence_score,
            retrieval_metadata=RetrievalMetadata(
                dense_candidates_count=len(retrieved_chunks),
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
