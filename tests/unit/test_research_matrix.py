"""Unit tests for Evidence Comparison Matrix construction and Markdown dossier exporter."""

import datetime

from backend.models.research import ResearchStudy
from backend.research.matrix import (
    build_comparison_matrix,
    determine_evidence_strength,
    export_markdown_dossier,
)


def test_determine_evidence_strength_levels() -> None:
    """Verifies Oxford CEBM evidence hierarchy classification."""
    # Systematic review -> High
    assert determine_evidence_strength("Systematic Review & Meta-Analysis", 5000) == "High"

    # Clinical guideline -> High
    assert determine_evidence_strength("Clinical Practice Guideline", None) == "High"

    # Large RCT (N >= 100) -> High
    assert determine_evidence_strength("Randomized Controlled Trial", 450) == "High"

    # Small RCT (N < 100) -> Moderate
    assert determine_evidence_strength("Randomized Controlled Trial", 48) == "Moderate"

    # Large Prospective Cohort (N >= 100) -> Moderate
    assert determine_evidence_strength("Prospective Cohort Study", 1200) == "Moderate"

    # Retrospective Cohort -> Low-Moderate
    assert determine_evidence_strength("Retrospective Cohort Study", 800) == "Low-Moderate"

    # Case report -> Preliminary
    assert determine_evidence_strength("Case Series / Report", 12) == "Preliminary"


def test_build_comparison_matrix() -> None:
    """Verifies side-by-side Evidence Comparison Matrix generation."""
    study1 = ResearchStudy(
        id="study_001",
        document_id="doc_001",
        title="ADA Empagliflozin Outcome Study",
        doi="10.1056/NEJMoa1504720",
        pmid="26378978",
        authors="Zinman B, et al.",
        publication_date=datetime.date(2015, 9, 17),
        study_design="Randomized Controlled Trial",
        sample_size=7020,
        population_description="Patients with type 2 diabetes and high cardiovascular risk",
        intervention="Empagliflozin (10 mg or 25 mg) vs placebo",
        primary_outcome="Death from cardiovascular causes, nonfatal MI, nonfatal stroke",
        limitations="Primarily Caucasian cohort; limited non-cardiovascular endpoints",
    )

    study2 = ResearchStudy(
        id="study_002",
        document_id="doc_002",
        title="Observational SGLT2i Real-World Effectiveness Cohort",
        doi="10.1016/S2213-8587(18)30065-0",
        pmid="29544990",
        authors="Kosiborod M, et al.",
        publication_date=datetime.date(2018, 5, 1),
        study_design="Prospective Cohort Study",
        sample_size=309440,
        population_description="Broad international real-world population with type 2 diabetes",
        intervention="SGLT-2 inhibitors vs other glucose-lowering drugs",
        primary_outcome="Hospitalization for heart failure and all-cause mortality",
        limitations="Potential residual confounding in observational registry linkage",
    )

    matrix = build_comparison_matrix([study1, study2], comparison_topic="Cardiovascular Outcomes of SGLT2 Inhibitors")

    assert matrix.studies_count == 2
    assert matrix.comparison_topic == "Cardiovascular Outcomes of SGLT2 Inhibitors"
    assert len(matrix.matrix_rows) == 2

    row1 = matrix.matrix_rows[0]
    assert row1.study_id == "study_001"
    assert row1.evidence_strength == "High"
    assert row1.sample_size == 7020

    row2 = matrix.matrix_rows[1]
    assert row2.study_id == "study_002"
    assert row2.evidence_strength == "Moderate"

    # Verifies synthesized findings summarize both studies
    assert "316,460" in matrix.synthesized_findings or "encompassing a collective cohort" in matrix.synthesized_findings
    assert matrix.guideline_alignment is not None


def test_export_markdown_dossier() -> None:
    """Verifies Markdown dossier exporter produces formatted tables and citation lists."""
    study = ResearchStudy(
        id="study_003",
        document_id="doc_003",
        title="FLAURA: Osimertinib in Untreated EGFR-Mutated Advanced NSCLC",
        doi="10.1056/NEJMoa1713137",
        pmid="29151359",
        authors="Soria JC, Ohe Y, Vansteenkiste J, et al.",
        publication_date=datetime.date(2018, 1, 11),
        study_design="Randomized Controlled Trial",
        sample_size=556,
        population_description="Previously untreated EGFR mutation-positive advanced NSCLC",
        intervention="Osimertinib (80 mg once daily) vs standard EGFR-TKI",
        primary_outcome="Progression-free survival (median 18.9 mo vs 10.2 mo; HR 0.46)",
        limitations="Unblinded design post-progression; crossover permitted",
    )

    matrix = build_comparison_matrix([study], comparison_topic="First-line EGFR-TKI in Advanced NSCLC")
    markdown_output = export_markdown_dossier(matrix, custom_title="FLAURA Clinical Evidence Dossier")

    assert "# FLAURA Clinical Evidence Dossier" in markdown_output
    assert "| Study Title | Design | Level | N | Population | Intervention | Primary Outcome | Limitations |" in markdown_output
    assert "Osimertinib" in markdown_output
    assert "`High`" in markdown_output
    assert "https://doi.org/10.1056/NEJMoa1713137" in markdown_output
    assert "https://pubmed.ncbi.nlm.nih.gov/29151359" in markdown_output
    assert "Bibliographic Citations & Verification Provenance" in markdown_output
