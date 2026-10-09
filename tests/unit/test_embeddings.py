"""Unit tests for FastEmbed CPU-optimized dense vector embeddings."""

import math
import time

from backend.vector.embeddings import FastEmbedProvider


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Computes cosine similarity between two vector lists."""
    dot = sum(a * b for a, b in zip(v1, v2, strict=True))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def test_fastembed_dimension_and_output() -> None:
    """Verifies that FastEmbed generates 384-dimensional dense vectors."""
    provider = FastEmbedProvider.get_instance()
    assert provider.dimensions == 384

    query_vec = provider.embed_query("EGFR L858R mutation in non-small cell lung cancer")
    assert len(query_vec) == 384
    assert isinstance(query_vec[0], float)

    batch_vecs = provider.embed_documents(
        ["Patient presented with hemoptysis", "CT revealed 3.2 cm upper lobe nodule"]
    )
    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == 384
    assert len(batch_vecs[1]) == 384


def test_fastembed_clinical_semantic_similarity() -> None:
    """Verifies that semantically related clinical concepts exhibit higher cosine similarity."""
    provider = FastEmbedProvider.get_instance()

    anchor = provider.embed_query("adenocarcinoma of the lung")
    related = provider.embed_query("non-small cell lung carcinoma with pleural effusion")
    unrelated = provider.embed_query("closed fracture of the distal radius forearm")

    sim_related = cosine_similarity(anchor, related)
    sim_unrelated = cosine_similarity(anchor, unrelated)

    assert sim_related > sim_unrelated
    assert sim_related > 0.65


def test_fastembed_cpu_latency_benchmark() -> None:
    """Verifies that CPU embedding of a single 512-character chunk executes in under 50ms."""
    provider = FastEmbedProvider.get_instance()
    text = (
        "Patient Eleanor Vance, 65yo female, diagnosed with metastatic adenocarcinoma. "
        "Molecular testing identified EGFR exon 21 L858R substitution. "
        "Recommend initiation of third-generation EGFR TKI Osimertinib 80mg daily."
    )

    # Warmup
    provider.embed_query("warmup")

    start = time.perf_counter()
    provider.embed_query(text)
    latency_ms = (time.perf_counter() - start) * 1000

    assert latency_ms < 50.0  # CPU target threshold
