# Patient360: Fifteen-Phase Implementation Roadmap

## 1. Overview & Timeline Strategy
The development of Patient360 is structured across fifteen distinct, verifiable engineering phases. Each phase is executed sequentially and validated against the 13-Point Definition of Done.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              PATIENT360 PHASE ROADMAP                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Foundation:    Phase 1 (Architecture) ──► Phase 2 (Foundation) ──► Phase 3 (Auth/RBAC) │
│ Ingestion:     Phase 4 (Doc/Patient CRUD) ──► Phase 5 (Parsing) ──► Phase 6 (Indexing) │
│ RAG Pipeline:  Phase 7 (Baseline RAG) ──► Phase 8 (Hybrid RAG)                         │
│ Intelligence:  Phase 9 (Timeline) ──► Phase 10 (Agents) ──► Phase 11 (Research)        │
│ Quality/Rel:   Phase 12 (Eval Lab) ──► Phase 13 (Security) ──► Phase 14 (Hardening)    │
│ Release:       Phase 15 (Portfolio & Demo Release)                                     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Phase Specifications

### Phase 1: Discovery, Requirements, and Architecture
* **Objectives:** Establish project charter, system requirements, modular architecture, database schema, API contracts, threat model, testing strategy, and phase tracking.
* **Prerequisites:** Empty workspace.
* **Deliverables:** Complete documentation suite in `docs/` (15 files).
* **Testing:** Markdown syntax, schema completeness, and link verification.
* **Acceptance Criteria:** All 15 documents authored; explicit user approval obtained.
* **Effort:** 1–2 days.
* **Risks:** Scope creep. *Mitigation:* Strict boundary between core MVP and optional features.

### Phase 2: Development Foundation and Tooling Setup
* **Objectives:** Initialize repository layout, configure backend (Python 3.11, FastAPI), frontend (Vite, React, TypeScript, Tailwind), Docker Compose infrastructure (Postgres, Qdrant), linting, typing, and test harnesses.
* **Prerequisites:** Phase 1 approved.
* **Deliverables:** `docker-compose.yml`, `backend/`, `frontend/`, `tests/conftest.py`, working `/health` endpoint.
* **Testing:** Health probe test verifying live connection to PostgreSQL and Qdrant.
* **Acceptance Criteria:** `docker compose up` starts healthy services; `pytest` passes; `npm run build` succeeds.
* **Effort:** 2–3 days.
* **Risks:** Docker port collisions on Windows. *Mitigation:* Standard mapped ports (5432, 6333, 8000, 5173).

### Phase 3: Authentication, Authorization, and RBAC
* **Objectives:** Implement JWT authentication, Argon2 password hashing, and server-side RBAC protecting all backend endpoints.
* **Prerequisites:** Phase 2 verified.
* **Deliverables:** `users` and `audit_logs` tables, Alembic migrations, `/auth/login`, `/auth/me`, security dependencies.
* **Testing:** Tests for invalid credentials (401), role mismatch (403), token expiration.
* **Acceptance Criteria:** Unauthenticated requests rejected; user roles properly enforced.
* **Effort:** 2–3 days.
* **Risks:** Insecure token storage. *Mitigation:* In-memory state and secure authorization headers.

### Phase 4: Patient and Document Management
* **Objectives:** Build patient record CRUD, PDF upload validation, document metadata storage, and server-side patient-level access isolation.
* **Prerequisites:** Phase 3 verified.
* **Deliverables:** `patients`, `documents`, and permissions tables, file storage adapter, upload endpoint.
* **Testing:** Tests verifying cross-patient access rejection and duplicate SHA-256 upload detection.
* **Acceptance Criteria:** Documents upload and persist cleanly; patient isolation strictly verified.
* **Effort:** 3–4 days.
* **Risks:** Malicious uploads. *Mitigation:* 25 MB file cap, magic byte verification.

### Phase 5: Document Ingestion, Parsing, and Chunking
* **Objectives:** Build an idempotent, page-aware PDF extraction and semantic chunking pipeline preserving document provenance.
* **Prerequisites:** Phase 4 verified.
* **Deliverables:** PyMuPDF extractor, clinical text normalizer, semantic chunker, `document_chunks` table.
* **Testing:** Unit tests verifying exact page-number tracking across multi-page PDFs; unit tests for clinical decimal preservation (`0.5 mg`).
* **Acceptance Criteria:** 100% of chunks retain accurate `page_number` references.
* **Effort:** 3–4 days.
* **Risks:** Multi-column layout scrambling. *Mitigation:* Layout-aware block extraction.

### Phase 6: Embeddings and Vector Indexing
* **Objectives:** Integrate FastEmbed CPU dense embeddings and configure Qdrant vector indexing with metadata payload filtering and idempotent reindexing.
* **Prerequisites:** Phase 5 verified.
* **Deliverables:** `FastEmbed` provider (`bge-small-en-v1.5`), Qdrant collection setup, vector indexing worker.
* **Testing:** Integration tests confirming vector upsert and payload-filtered searches isolate patient chunks.
* **Acceptance Criteria:** FastEmbed encodes on CPU in $< 20\text{ ms}$ per chunk; payload filtering returns zero chunks from other patients.
* **Effort:** 2–3 days.
* **Risks:** Drift between SQL and Qdrant. *Mitigation:* Transactional cleanup hooks.

### Phase 7: Baseline Grounded RAG
* **Objectives:** Implement an end-to-end question-answering workflow with dense vector retrieval, grounded prompt construction, LLM adapter, and basic citation generation.
* **Prerequisites:** Phase 6 verified.
* **Deliverables:** `BaseLLMProvider` interface, `MockLLMProvider`, hosted API adapter, prompt builder, `/rag/query` endpoint.
* **Testing:** Tests asserting that questions without supporting evidence return the standard abstention message.
* **Acceptance Criteria:** End-to-end query returns grounded answer with page citations; mock provider passes in CI.
* **Effort:** 3–4 days.
* **Risks:** Hallucinated clinical facts. *Mitigation:* Zero temperature, strict grounding prompts.

### Phase 8: Advanced Hybrid RAG and Retrieval Optimization
* **Objectives:** Integrate in-memory BM25 sparse retrieval, Reciprocal Rank Fusion (RRF), post-retrieval deduplication, and automated citation verification.
* **Prerequisites:** Phase 7 verified.
* **Deliverables:** BM25 indexer, RRF merger, automated `CitationVerifier`, frontend PDF viewer with clickable citations.
* **Testing:** Benchmark comparison proving hybrid RRF outperforms dense-only search on exact medical abbreviations.
* **Acceptance Criteria:** Hybrid search retrieves exact keyword matches missed by dense search; clickable citations open corresponding PDF page.
* **Effort:** 3–4 days.
* **Risks:** BM25 memory growth. *Mitigation:* Partition index per-patient.

### Phase 9: Longitudinal Patient Timeline and Clinical Event Synthesis
* **Objectives:** Extract dated clinical events, distinguish event dates from document dates, generate chronological summaries, and surface clinical contradictions.
* **Prerequisites:** Phase 8 verified.
* **Deliverables:** Clinical event extractor, `clinical_events` table, contradiction detector, interactive frontend Timeline view.
* **Testing:** Unit tests verifying contradiction flag is raised when Doc A and Doc B present conflicting allergy notes.
* **Acceptance Criteria:** Timeline displays events chronologically with citations; contradictions clearly highlighted.
* **Effort:** 4–5 days.
* **Risks:** Complex temporal expressions. *Mitigation:* Document date fallback with precision tagging.

### Phase 10: Bounded Agentic Workflows
* **Objectives:** Implement bounded, observable multi-step research and reconciliation workflows using LangGraph with strict execution budgets and human-in-the-loop review.
* **Prerequisites:** Phase 9 verified.
* **Deliverables:** LangGraph state graph, read-only tools, step limit guards (max 5), human approval gate.
* **Testing:** Tests verifying workflow halts at 5 iterations if unresolved.
* **Acceptance Criteria:** Workflow completes multi-step retrieval deterministically; human approval required before finalizing synthesis.
* **Effort:** 4–5 days.
* **Risks:** Infinite loops. *Mitigation:* Hard state machine loop counter.

### Phase 11: Medical Research Intelligence
* **Objectives:** Ingest medical research papers and clinical guidelines, extract study methodologies, and generate structured comparative evidence matrices.
* **Prerequisites:** Phase 10 verified.
* **Deliverables:** `research_studies` table, study parameter extractor, `/research/compare` endpoint, Markdown dossier exporter.
* **Testing:** Tests verifying extraction of sample sizes and trial arms across sample study PDFs.
* **Acceptance Criteria:** Multi-study comparison table renders cleanly with side-by-side methodology and limitation columns.
* **Effort:** 3–4 days.
* **Risks:** Academic PDF layout variations. *Mitigation:* Layout-aware text extraction.

### Phase 12: Comprehensive Evaluation Laboratory and Quality Assurance
* **Objectives:** Formalize the automated benchmark runner, execute the 50-item synthetic benchmark, measure retrieval and generation metrics, and build the Evaluation Lab dashboard.
* **Prerequisites:** Phase 11 verified.
* **Deliverables:** Benchmark runner (`evaluation/runners/`), metric calculators, `evaluation_runs` table, frontend Evaluation Lab.
* **Testing:** Automated CI job asserting Faithfulness $\ge 0.85$ and Citation Precision $\ge 0.90$ on synthetic benchmark.
* **Acceptance Criteria:** Complete reproducible benchmark run with metrics saved to DB; frontend renders comparison charts.
* **Effort:** 3–4 days.
* **Risks:** Metric non-determinism. *Mitigation:* Zero temperature and frozen ground-truth dataset.

### Phase 13: Security Hardening, Privacy Review, and Responsible AI
* **Objectives:** Execute STRIDE threat mitigation audits, conduct adversarial prompt-injection testing, verify zero-PHI logging, and enforce data retention and deletion workflows.
* **Prerequisites:** Phase 12 verified.
* **Deliverables:** Rate limiting, audit log sanitizer, cascading deletion service, safety disclaimers, emergency escalation filter.
* **Testing:** Adversarial prompt-injection test suite; cross-tenant access penetration tests.
* **Acceptance Criteria:** Zero prompt injections succeed; 100% of cross-patient access attempts rejected with 403 Forbidden.
* **Effort:** 3–4 days.
* **Risks:** Leakage in error messages. *Mitigation:* Generic sanitized error schemas.

### Phase 14: Production Hardening, Observability, and Deployment
* **Objectives:** Optimize application performance, implement Prometheus metrics and structured JSON logging, configure multi-stage Dockerfiles, and provide CI/CD workflows.
* **Prerequisites:** Phase 13 verified.
* **Deliverables:** Multi-stage Dockerfiles, production Docker Compose, Nginx config, Prometheus `/metrics` endpoint, GitHub Actions workflow.
* **Testing:** Full build and startup test of the production Docker Compose stack.
* **Acceptance Criteria:** All services start cleanly under production configuration with restart policies; CI passes.
* **Effort:** 3–4 days.
* **Risks:** Container memory bloat. *Mitigation:* Strict container memory limits (512M).

### Phase 15: Final Polish, Documentation, and Portfolio Release
* **Objectives:** Finalize accessibility and UI polish, assemble synthetic demo datasets, write comprehensive user documentation, record demo walkthrough, and deliver release artifacts.
* **Prerequisites:** Phase 14 verified.
* **Deliverables:** Pre-seeded synthetic demo data, comprehensive `README.md`, portfolio case study, verified benchmark results.
* **Testing:** Full end-to-end user journey walkthrough across all 4 personas on a clean installation.
* **Acceptance Criteria:** Seamless local setup via a single command; verified demonstration data pre-loaded; all documentation truthful.
* **Effort:** 2–3 days.
* **Risks:** Outdated setup instructions. *Mitigation:* Clean environment validation.
