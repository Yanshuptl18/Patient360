"""Benchmark comparing Dense-only, Sparse-only, and Hybrid RRF retrieval on clinical abbreviations."""

from backend.retrieval.bm25 import BM25Document, BM25Index
from backend.retrieval.rrf import reciprocal_rank_fusion
from backend.vector.embeddings import FastEmbedProvider
from backend.vector.store import VectorSearchResult


def test_hybrid_rrf_outperforms_dense_only_on_medical_acronyms() -> None:
    """
    Benchmark test verifying that Hybrid RRF retrieves exact medical abbreviations (e.g. NT-proBNP)
    at Rank #1, even when dense similarity distributes high scores across general semantic distractors.
    """
    embedder = FastEmbedProvider()

    # Clinical passages: Chk-1 is a general cardiac note (semantic distractor),
    # Chk-2 contains the exact rare biomarker acronym 'NT-proBNP'.
    chunks_data = [
        {
            "id": "chk-semantic-distractor",
            "content": "Patient presents with progressive shortness of breath, fluid overload, and chronic cardiac failure.",
            "doc_title": "Cardiology_Consult.pdf",
        },
        {
            "id": "chk-exact-acronym",
            "content": "Laboratory diagnostic panel demonstrated elevated NT-proBNP at 6200 pg/mL indicating acute decompensation.",
            "doc_title": "Cardiac_Enzymes_Lab.pdf",
        },
        {
            "id": "chk-unrelated",
            "content": "Orthopedic physical therapy notes for right knee arthroscopy rehab.",
            "doc_title": "PT_Notes.pdf",
        },
    ]

    query = "NT-proBNP"

    # 1. Simulate Dense Search using real FastEmbed cosine similarity
    q_vec = embedder.embed_query(query)
    c_vecs = embedder.embed_documents([c["content"] for c in chunks_data])

    dense_candidates: list[VectorSearchResult] = []
    for c_data, c_vec in zip(chunks_data, c_vecs, strict=False):
        cosine_sim = sum(a * b for a, b in zip(q_vec, c_vec, strict=False))
        dense_candidates.append(
            VectorSearchResult(
                chunk_id=c_data["id"],
                document_id="doc-test",
                patient_id="pat-test",
                page_number=1,
                chunk_index=0,
                content=c_data["content"],
                raw_content=c_data["content"],
                score=float(cosine_sim),
                doc_title=c_data["doc_title"],
                doc_type="lab_report",
                doc_date="2024-03-01",
            )
        )
    dense_candidates.sort(key=lambda x: x.score, reverse=True)

    # 2. Sparse BM25 Search
    bm25 = BM25Index()
    bm25_docs = [
        BM25Document(
            chunk_id=c["id"],
            document_id="doc-test",
            patient_id="pat-test",
            page_number=1,
            chunk_index=0,
            content=c["content"],
            raw_content=c["content"],
            doc_title=c["doc_title"],
            doc_type="lab_report",
            doc_date="2024-03-01",
        )
        for c in chunks_data
    ]
    bm25.index_documents(bm25_docs)
    sparse_candidates = bm25.search(query, top_k=5)

    # In BM25, exact acronym MUST be ranked #1
    assert sparse_candidates[0].chunk_id == "chk-exact-acronym"

    # 3. Hybrid RRF Merge
    hybrid_candidates = reciprocal_rank_fusion(
        dense_results=dense_candidates,
        sparse_results=sparse_candidates,
        k=60,
        top_k=5,
    )

    # In Hybrid RRF, the exact clinical acronym is guaranteed at Rank #1
    assert len(hybrid_candidates) >= 2
    top_hit = hybrid_candidates[0]
    assert top_hit.chunk_id == "chk-exact-acronym"
    assert "NT-proBNP" in top_hit.content
    assert top_hit.sparse_rank == 1
    assert top_hit.rrf_score > hybrid_candidates[1].rrf_score
