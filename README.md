# Patient360: Healthcare Intelligence & Grounded RAG Platform

> **Clinical Notice:** Patient360 is an informational retrieval and evidence synthesis platform. It is NOT a medical device, diagnostic tool, or clinical prescription system. All assertions must be reviewed by qualified healthcare professionals against source clinical documentation.

---

## 1. Project Overview
Patient360 is an enterprise-grade, evidence-grounded healthcare intelligence platform powered by Generative AI, Retrieval-Augmented Generation (RAG), bounded agentic workflows, and clinical NLP. The platform turns fragmented healthcare records (consultation notes, lab narratives, discharge summaries) and biomedical research literature into structured, searchable, traceable, evidence-grounded knowledge with guaranteed page-level citations.

---

## 2. Key Capabilities
* **Patient Document Intelligence:** Idempotent PDF ingestion preserving page-level provenance; dual-mode hybrid retrieval (Dense FastEmbed + Sparse BM25 + Reciprocal Rank Fusion).
* **Longitudinal Patient History:** Chronological clinical event extraction with explicit separation of event dates from document dates; surfacing conflicting facts and clinical ambiguities.
* **Medical Research Intelligence:** Cross-study literature retrieval, structured study parameter extraction, and comparative evidence synthesis matrices.
* **Bounded Agentic Workflows:** Deterministic LangGraph state machine with iteration bounds (max 5), 30s timeout, read-only tools, and human-in-the-loop review gates.
* **Evaluation Laboratory:** Version-controlled 50-item synthetic benchmark measuring Recall@K, MRR, Faithfulness, Citation Precision, latency, and cost.

---

## 3. Architecture & Documentation Hierarchy

All architectural specifications, designs, and operational policies are formally maintained in the [`docs/`](file:///e:/project/Patient360/docs) directory:

| Document | Description |
| :--- | :--- |
| [PROJECT_CHARTER.md](file:///e:/project/Patient360/docs/PROJECT_CHARTER.md) | Vision, problem statement, core pillars, non-goals, and governance |
| [REQUIREMENTS.md](file:///e:/project/Patient360/docs/REQUIREMENTS.md) | Detailed functional and non-functional requirements with traceability |
| [ARCHITECTURE.md](file:///e:/project/Patient360/docs/ARCHITECTURE.md) | System component boundaries, Mermaid interaction flows, and sequence diagrams |
| [DATA_MODEL.md](file:///e:/project/Patient360/docs/DATA_MODEL.md) | PostgreSQL schema DDL, entity relationships, Qdrant payload schema |
| [API_SPECIFICATION.md](file:///e:/project/Patient360/docs/API_SPECIFICATION.md) | OpenAPI REST endpoints, payload schemas, error formats |
| [THREAT_MODEL.md](file:///e:/project/Patient360/docs/THREAT_MODEL.md) | STRIDE threat analysis, prompt injection defense, isolation architecture |
| [PRIVACY_AND_SAFETY.md](file:///e:/project/Patient360/docs/PRIVACY_AND_SAFETY.md) | Healthcare safety policies, disclaimers, de-identification standards |
| [RAG_DESIGN.md](file:///e:/project/Patient360/docs/RAG_DESIGN.md) | Chunking strategy, FastEmbed CPU vectors, BM25, RRF math, citation verifier |
| [EVALUATION_PLAN.md](file:///e:/project/Patient360/docs/EVALUATION_PLAN.md) | 50-item synthetic benchmark dataset, metric formulas, and target thresholds |
| [TEST_STRATEGY.md](file:///e:/project/Patient360/docs/TEST_STRATEGY.md) | Automated testing pyramid (unit, integration, security, e2e) |
| [DEPLOYMENT.md](file:///e:/project/Patient360/docs/DEPLOYMENT.md) | Local development setup for Windows 16GB CPU and production guidelines |
| [DECISIONS.md](file:///e:/project/Patient360/docs/DECISIONS.md) | Architectural Decision Records (ADRs 001 through 012) |
| [ROADMAP.md](file:///e:/project/Patient360/docs/ROADMAP.md) | Detailed fifteen-phase roadmap with deliverables, tests, and risks |
| [PROJECT_STATUS.md](file:///e:/project/Patient360/docs/PROJECT_STATUS.md) | Active phase tracker and Definition of Done verification log |
| [KNOWN_LIMITATIONS.md](file:///e:/project/Patient360/docs/KNOWN_LIMITATIONS.md) | Technical boundaries, CPU constraints, and scope boundaries |

---

## 4. Current Phase Status
* **Current Active Phase:** **Phase 1: Discovery, Requirements, and Architecture** (Completed, Pending User Approval).
* **Next Phase:** **Phase 2: Development Foundation and Tooling Setup**.
