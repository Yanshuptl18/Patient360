"""Unit tests for Qdrant vector store adapter, collection management, and payload filtering."""

from qdrant_client import QdrantClient

from backend.models.chunk import DocumentChunk
from backend.vector.embeddings import FastEmbedProvider
from backend.vector.store import QdrantVectorStore


def test_qdrant_vector_store_collection_and_upsert() -> None:
    """Verifies collection creation, vector upsert, and payload metadata preservation."""
    mem_client = QdrantClient(":memory:")
    embedder = FastEmbedProvider.get_instance()
    store = QdrantVectorStore(
        client=mem_client,
        embedder=embedder,
        collection_name="test_collection_unit",
    )

    stats = store.get_collection_stats()
    assert stats["status"] == "UP"
    assert stats["dimensions"] == 384

    # Create mock chunks
    chunk1 = DocumentChunk(
        id="c1111111-1111-1111-1111-111111111111",
        document_id="d1111111-1111-1111-1111-111111111111",
        chunk_index=0,
        page_number=1,
        content="Patient has EGFR exon 21 L858R mutation.",
        raw_content="Patient has EGFR exon 21 L858R mutation.",
        token_count=10,
        metadata_json={
            "patient_id": "p-alpha",
            "doc_title": "Biomarker Report",
            "doc_type": "lab_report",
            "doc_date": "2024-01-10",
        },
    )
    chunk2 = DocumentChunk(
        id="c2222222-2222-2222-2222-222222222222",
        document_id="d2222222-2222-2222-2222-222222222222",
        chunk_index=0,
        page_number=1,
        content="Patient was treated for fracture of left distal radius.",
        raw_content="Patient was treated for fracture of left distal radius.",
        token_count=11,
        metadata_json={
            "patient_id": "p-beta",
            "doc_title": "Orthopedic Note",
            "doc_type": "patient_record",
            "doc_date": "2024-02-14",
        },
    )

    upserted = store.upsert_chunks([chunk1, chunk2])
    assert upserted == 2

    stats_after = store.get_collection_stats()
    assert stats_after["vectors_count"] == 2


def test_qdrant_patient_payload_isolation() -> None:
    """Verifies that patient-filtered vector search isolates patient cohorts."""
    mem_client = QdrantClient(":memory:")
    embedder = FastEmbedProvider.get_instance()
    store = QdrantVectorStore(
        client=mem_client,
        embedder=embedder,
        collection_name="test_isolation_unit",
    )

    chunk_a = DocumentChunk(
        id="c3333333-3333-3333-3333-333333333333",
        document_id="d3333333-3333-3333-3333-333333333333",
        chunk_index=0,
        page_number=1,
        content="Severe allergic reaction to penicillin with anaphylaxis.",
        raw_content="Severe allergic reaction to penicillin with anaphylaxis.",
        token_count=8,
        metadata_json={"patient_id": "patient-a"},
    )
    chunk_b = DocumentChunk(
        id="c4444444-4444-4444-4444-444444444444",
        document_id="d4444444-4444-4444-4444-444444444444",
        chunk_index=0,
        page_number=1,
        content="Patient has known penicillin allergy documented in 2021.",
        raw_content="Patient has known penicillin allergy documented in 2021.",
        token_count=9,
        metadata_json={"patient_id": "patient-b"},
    )
    store.upsert_chunks([chunk_a, chunk_b])

    # Search for penicillin allergy filtering for patient-a
    results_a = store.search(query="penicillin allergy", patient_id="patient-a", top_k=5)
    assert len(results_a) == 1
    assert results_a[0].patient_id == "patient-a"
    assert results_a[0].chunk_id == "c3333333-3333-3333-3333-333333333333"

    # Search for penicillin allergy filtering for patient-b
    results_b = store.search(query="penicillin allergy", patient_id="patient-b", top_k=5)
    assert len(results_b) == 1
    assert results_b[0].patient_id == "patient-b"
    assert results_b[0].chunk_id == "c4444444-4444-4444-4444-444444444444"

    # Search filtering for patient-c (no records)
    results_c = store.search(query="penicillin allergy", patient_id="patient-c", top_k=5)
    assert len(results_c) == 0


def test_qdrant_delete_document_chunks() -> None:
    """Verifies that deleting a document purges all its vectors from the collection."""
    mem_client = QdrantClient(":memory:")
    embedder = FastEmbedProvider.get_instance()
    store = QdrantVectorStore(
        client=mem_client,
        embedder=embedder,
        collection_name="test_delete_unit",
    )

    chunk = DocumentChunk(
        id="c5555555-5555-5555-5555-555555555555",
        document_id="doc-to-delete",
        chunk_index=0,
        page_number=1,
        content="Temporary document content.",
        raw_content="Temporary document content.",
        token_count=4,
        metadata_json={"patient_id": "p-del"},
    )
    store.upsert_chunks([chunk])
    assert store.get_collection_stats()["vectors_count"] == 1

    store.delete_document_chunks("doc-to-delete")
    assert store.get_collection_stats()["vectors_count"] == 0
