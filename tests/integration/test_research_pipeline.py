"""Integration tests for Medical Research Intelligence pipeline, comparison matrix, and export."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.chunk import DocumentChunk
from backend.models.document import Document


def create_mock_research_doc(
    db: Session,
    title: str,
    chunks_text: list[str],
) -> Document:
    """Helper to persist a test research publication document with chunks."""
    doc = Document(
        title=title,
        file_path=f"/mock_storage/{title.lower().replace(' ', '_')}.pdf",
        file_hash_sha256="mock_sha256_" + title[:10],
        file_size_bytes=102400,
        mime_type="application/pdf",
        doc_type="research_paper",
        ingestion_status="completed",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    for idx, text in enumerate(chunks_text, 1):
        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=idx,
            page_number=idx,
            content=text,
            raw_content=text,
            token_count=len(text.split()),
            metadata_json={"title": title},
        )
        db.add(chunk)
    db.commit()
    return doc


def test_research_pipeline_full_lifecycle(
    client: TestClient,
    reviewer_headers: dict[str, str],
    db: Session,
) -> None:
    """Verifies end-to-end study extraction, comparative matrix generation, and dossier export."""
    # 1. Create two mock research publications in DB
    doc1 = create_mock_research_doc(
        db=db,
        title="Osimertinib in Resected EGFR-Mutated NSCLC (ADAURA Trial)",
        chunks_text=[
            (
                "ADAURA Trial Investigators. N Engl J Med 2020; 383:1711-1723.\n"
                "DOI: 10.1056/NEJMoa2027071\n"
                "PMID: 32951379\n"
                "Methods: In this double-blind, randomized controlled trial, a total of 682 patients with stage IB to IIIA EGFR mutation-positive NSCLC were enrolled.\n"
                "Interventions: Patients were randomly assigned to receive osimertinib (80 mg once daily) or matching placebo for up to 3 years.\n"
                "Results: Disease-free survival was significantly longer with osimertinib than with placebo (HR 0.20; 95% CI, 0.14 to 0.30; P<0.001).\n"
                "Limitations: Overall survival data were immature at the time of primary analysis.\n"
            )
        ],
    )

    doc2 = create_mock_research_doc(
        db=db,
        title="Adjuvant Gefitinib vs Vinorelbine plus Cisplatin in EGFR-Mutant NSCLC (ADJUVANT-CTONG1104)",
        chunks_text=[
            (
                "ADJUVANT / CTONG1104 Trial. Lancet Oncol 2018; 19: 139-148.\n"
                "DOI: 10.1016/S1470-2045(17)30729-5\n"
                "PMID: 29174310\n"
                "Methods: A randomized controlled trial conducted across 27 centers in China. A total of 222 patients aged 18 to 75 years were randomized.\n"
                "Interventions: Adjuvant gefitinib (250 mg once daily for 24 months) vs vinorelbine plus cisplatin.\n"
                "Results: Median disease-free survival was 28.7 months with gefitinib vs 18.0 months with chemotherapy (HR 0.60; P=0.0054).\n"
                "Limitations: Follow-up showed no statistically significant difference in final overall survival.\n"
            )
        ],
    )

    # 2. Extract Study 1
    extract_resp1 = client.post(
        f"/api/v1/research/extract/{doc1.id}",
        headers=reviewer_headers,
    )
    assert extract_resp1.status_code == 200
    study1_data = extract_resp1.json()
    assert study1_data["doi"] == "10.1056/NEJMoa2027071"
    assert study1_data["pmid"] == "32951379"
    assert study1_data["sample_size"] == 682
    assert study1_data["study_design"] == "Randomized Controlled Trial"
    study1_id = study1_data["id"]

    # 3. Extract Study 2
    extract_resp2 = client.post(
        f"/api/v1/research/extract/{doc2.id}",
        headers=reviewer_headers,
    )
    assert extract_resp2.status_code == 200
    study2_data = extract_resp2.json()
    assert study2_data["doi"] == "10.1016/S1470-2045(17)30729-5"
    assert study2_data["sample_size"] == 222
    study2_id = study2_data["id"]

    # 4. List Research Studies
    list_resp = client.get("/api/v1/research/studies", headers=reviewer_headers)
    assert list_resp.status_code == 200
    studies_list = list_resp.json()
    study_ids = [s["id"] for s in studies_list]
    assert study1_id in study_ids
    assert study2_id in study_ids

    # 5. Fetch Individual Study
    get_resp = client.get(f"/api/v1/research/studies/{study1_id}", headers=reviewer_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == study1_id

    # 6. Generate Side-by-Side Comparison Matrix
    compare_resp = client.post(
        "/api/v1/research/compare",
        headers=reviewer_headers,
        json={
            "study_ids": [study1_id, study2_id],
            "comparison_topic": "Adjuvant EGFR-TKI in Resected NSCLC",
        },
    )
    assert compare_resp.status_code == 200
    matrix = compare_resp.json()
    assert matrix["studies_count"] == 2
    assert matrix["comparison_topic"] == "Adjuvant EGFR-TKI in Resected NSCLC"
    assert len(matrix["matrix_rows"]) == 2
    # Verify evidence levels
    for row in matrix["matrix_rows"]:
        assert row["evidence_strength"] == "High"  # Both are RCTs with N >= 100

    # 7. Export Research Synthesis Dossier
    export_resp = client.post(
        "/api/v1/research/export",
        headers=reviewer_headers,
        json={
            "study_ids": [study1_id, study2_id],
            "comparison_topic": "Adjuvant EGFR-TKI in Resected NSCLC",
            "title": "Adjuvant Targeted Therapy Synthesis Dossier",
        },
    )
    assert export_resp.status_code == 200
    dossier = export_resp.json()
    assert dossier["title"] == "Adjuvant Targeted Therapy Synthesis Dossier"
    assert dossier["studies_included_count"] == 2
    assert "# Adjuvant Targeted Therapy Synthesis Dossier" in dossier["markdown_content"]
    assert "| Study Title | Design | Level |" in dossier["markdown_content"]
    assert "https://doi.org/10.1056/NEJMoa2027071" in dossier["markdown_content"]


def test_research_endpoints_require_authentication(client: TestClient) -> None:
    """Verifies that unauthenticated requests to research endpoints are rejected with 401."""
    assert client.get("/api/v1/research/studies").status_code == 401
    assert client.post("/api/v1/research/compare", json={"study_ids": ["s1"]}).status_code == 401
    assert client.post("/api/v1/research/export", json={"study_ids": ["s1"]}).status_code == 401
