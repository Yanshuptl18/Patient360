# Patient360: Project Status and Phase Tracker

## 1. Master Phase Tracker

| Phase | Phase Name | Status | Prerequisites | Key Deliverables | Verification Evidence | Approval Status |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| **1** | Discovery, Requirements & Architecture | **Verified** | Empty workspace | 15 docs in `docs/`, architecture diagrams, data models | Phase 1 document review completed | Approved |
| **2** | Development Foundation & Tooling Setup | **Verified** | Phase 1 | Docker compose, FastAPI skeleton, React/Vite, health probes | Pytest 5/5 passed, Ruff clean, Mypy clean, Vite built | Approved |
| **3** | Authentication, Authorization & RBAC | **Verified** | Phase 2 | JWT auth, Argon2, RBAC guards, user tables, audit logger | 20/20 Pytest passed, Ruff clean, Mypy clean, Vite built | Approved |
| **4** | Patient & Document Management | **Verified** | Phase 3 | Patient CRUD, PDF upload, storage adapter, cohort isolation | 33/33 Pytest passed, Ruff clean, Mypy clean, Vite built | Approved |
| **5** | Document Ingestion, Parsing & Chunking | **Verified** | Phase 4 | PyMuPDF extractor, normalizer, semantic chunker | 48/48 Pytest passed, Ruff clean, Mypy clean, Vite built | Approved |
| **6** | Embeddings & Vector Indexing | **Verified** | Phase 5 | FastEmbed CPU provider, Qdrant collection, payload search, SemanticSearchModal | 56/56 Pytest passed, Ruff clean, Mypy clean, Vite built | Approved |
| **7** | **Baseline Grounded RAG** | **Completed** | Phase 6 | BaseLLMProvider, MockLLMProvider, GroundedPromptBuilder, CitationVerifier, ClinicalRAGPanel | 67/67 Pytest passed, Ruff clean, Mypy clean (74 files), Vite built in 5.58s | Pending Approval |
| **8** | Advanced Hybrid RAG & Retrieval Opt. | Planned | Phase 7 | In-memory BM25, RRF merger, citation verifier | Pending Phase 8 | Planned |
| **9** | Longitudinal Timeline & Clinical Events | Planned | Phase 8 | Event extractor, contradiction detector, Timeline UI | Pending Phase 9 | Planned |
| **10**| Bounded Agentic Workflows | Planned | Phase 9 | LangGraph state graph, read-only tools, approval gate | Pending Phase 10 | Planned |
| **11**| Medical Research Intelligence | Planned | Phase 10 | Research schema, comparative matrix, dossier exporter | Pending Phase 11 | Planned |
| **12**| Comprehensive Evaluation Laboratory | Planned | Phase 11 | 50-item benchmark runner, metrics, Evaluation Lab UI | Pending Phase 12 | Planned |
| **13**| Security Hardening & Responsible AI | Planned | Phase 12 | STRIDE pen-tests, prompt injection defense, deletion purge | Pending Phase 13 | Planned |
| **14**| Production Hardening & Observability | Planned | Phase 13 | Multi-stage Dockerfiles, Prometheus metrics, CI/CD | Pending Phase 14 | Planned |
| **15**| Final Polish, Demo Data & Release | Planned | Phase 14 | Synthetic demo cohorts, portfolio docs, release artifacts | Pending Phase 15 | Planned |

---

## 2. Phase 1 Verification Checklist (Definition of Done)
*Status: Verified and Approved*

---

## 3. Phase 2 Verification Checklist (Definition of Done)
*Status: Verified and Approved*

---

## 4. Phase 3 Verification Checklist (Definition of Done)

- [x] **1. Requirements & Scope Documented:** RBAC, JWT, and password hashing aligned with FR-AUTH requirements.
- [x] **2. Modular Architecture Enforced:** Models (`backend/models/user.py`, `backend/models/audit.py`), Schemas (`backend/schemas/auth.py`), Security (`backend/core/security.py`), Services (`backend/auth/`, `backend/audit/`), Dependencies (`backend/api/deps.py`), and Routes (`backend/api/v1/auth.py`).
- [x] **3. No Secrets / Real PHI Committed:** Passwords hashed with bcrypt; JWT signed via parameterized secret; zero PHI logged in audit trails.
- [x] **4. Dependencies Documented:** `email-validator>=2.1.0` added to `requirements.txt`.
- [x] **5. Automated Tests Passing:** 20/20 pytest tests pass (unit tests for security/tokens, integration tests for login, /me, token refresh, audit logging, and RBAC 401/403 rejection).
- [x] **6. Static Checks Passing:**
  - Python: `ruff check backend tests` passed with 0 errors.
  - Python: `mypy backend` passed with 0 errors (strict mode across 23 source files).
  - Frontend: `tsc --noEmit` passed with 0 errors.
  - Frontend: `vite build` produced optimized bundle in 2.95s.
- [x] **7. Security & Isolation Enforced:** Server-side RBAC dependencies (`require_role`, `require_roles`) reject unauthorized roles with 403 Forbidden; missing/invalid tokens reject with 401 Unauthorized.
- [x] **8. Error Handling & Edge Cases:** Expired tokens, tampered signatures, and inactive users handled with standard JSON error structures.
- [x] **9. Audit Trail Active:** Append-only database audit logs record `LOGIN_SUCCESS`, `LOGIN_ATTEMPT`, and `USER_PROVISIONED` events.
- [x] **10. Frontend Auth UI Integrated:** Interactive `LoginModal` with 1-click persona switching (Clinical Reviewer, Medical Researcher, Admin, Demo User) and live authenticated session banner.
- [x] **11. Known Limitations Recorded:** Refresh token rotation uses standard JWT claims; production SSO/OIDC integration deferred to Phase 14.
- [x] **12. Phase Tracker Updated:** Phase 3 marked Completed (Pending Approval).
- [x] **13. Explicit User Approval Requested:** Phase 3 approved by user.

---

## 5. Phase 4 Verification Checklist (Definition of Done)

- [x] **1. Requirements & Scope Documented:** Patient CRUD, user-patient permission boundaries, PDF format/size validation, and hash-partitioned storage aligned with FR-DOC and PRIVACY_AND_SAFETY requirements.
- [x] **2. Modular Architecture Enforced:**
  - Models: `backend/models/patient.py` (`Patient`, `UserPatientPermission`), `backend/models/document.py` (`Document`).
  - Schemas: `backend/schemas/patient.py`, `backend/schemas/document.py`.
  - Storage & Validation: `backend/documents/validator.py` (`validate_pdf_file`), `backend/documents/storage.py` (`DocumentStorage`).
  - Services: `backend/patients/service.py`, `backend/documents/service.py`.
  - API Routes: `backend/api/v1/patients.py`, `backend/api/v1/documents.py`.
- [x] **3. No Secrets / Real PHI Committed:** All patient profiles use synthetic MRNs (`SYN-XXXXXX`); zero real PHI stored; original PDFs stored in local volume with SHA-256 integrity checks.
- [x] **4. Dependencies Documented:** `python-multipart>=0.0.9` verified in `requirements.txt`.
- [x] **5. Automated Tests Passing:** 33/33 pytest tests pass:
  - `tests/unit/test_storage.py` (5 tests): PDF validation, magic bytes `%PDF-`, size rejection, directory traversal defense, file persistence.
  - `tests/integration/test_patients.py` (4 tests): Patient creation, synthetic MRN conflict rejection, server-side tenant isolation, RBAC access checks.
  - `tests/integration/test_documents.py` (4 tests): Upload valid PDF, duplicate hash idempotency, binary streaming download, cross-patient access boundary enforcement.
- [x] **6. Static Checks Passing:**
  - Python: `ruff check backend tests` passed with 0 errors.
  - Python: `mypy backend` passed with 0 errors across 35 source files.
  - Frontend: `npm run build` (`tsc && vite build`) produced production bundle in 3.06s with 0 errors.
- [x] **7. Security & Isolation Enforced:** Non-admin users can ONLY list and retrieve patients explicitly granted in `user_patient_permissions`. Attempts to fetch or upload documents across patient boundaries return `403 Forbidden`. Path traversal (`../`) is blocked at the storage layer.
- [x] **8. Error Handling & Edge Cases:** Non-PDF uploads rejected with `INVALID_DOCUMENT` (400), files >25MB rejected, duplicate uploads deduplicated idempotently without creating redundant physical files.
- [x] **9. Audit Trail Active:** Document uploads and patient registrations logged to immutable audit table with actor ID, patient ID, and SHA-256 hash.
- [x] **10. Frontend Workspace Integrated:**
  - Interactive Patient Dossier explorer with search, synthetic MRN badge, and `+ New Patient` modal.
  - Attached Document list with document type badges, file size format, ingestion status badge, download streaming action, and upload dropzone modal.
- [x] **11. Known Limitations Recorded:** Document parsing and vector embedding are deferred to Phase 5 and Phase 6; uploaded PDFs are registered with status `pending`.
- [x] **12. Phase Tracker Updated:** Phase 4 marked Completed (Pending Approval).
- [x] **13. Explicit User Approval Requested:** Phase 4 approved by user.

---

## 6. Phase 5 Verification Checklist (Definition of Done)

- [x] **1. Requirements & Scope Documented:** Page-aware text extraction, clinical normalization, sliding-window chunking, context header injection, and physical page provenance aligned with FR-DOC-01..07 and RAG_DESIGN requirements.
- [x] **2. Modular Architecture Enforced:**
  - Models: `backend/models/chunk.py` (`DocumentChunk`), updated `backend/models/document.py` (`chunks` cascade relationship).
  - Schemas: `backend/schemas/chunk.py` (`ChunkResponse`, `IngestionResponse`).
  - Ingestion Modules: `backend/ingestion/extractor.py` (`extract_pages_from_pdf`), `backend/ingestion/normalizer.py` (`normalize_clinical_text`), `backend/ingestion/chunker.py` (`SemanticChunker`, `split_into_clinical_sentences`), `backend/ingestion/service.py` (`ingest_document`).
  - API Routes: `POST /api/v1/documents/{id}/ingest`, `GET /api/v1/documents/{id}/chunks`.
- [x] **3. No Secrets / Real PHI Committed:** All test payloads and documents use synthetic patients (`SYN-INGEST-01`, `Eleanor Vance`); zero real PHI stored.
- [x] **4. Dependencies Documented:** `PyMuPDF>=1.24.0` verified in virtual environment.
- [x] **5. Automated Tests Passing:** **48/48 pytest tests pass** (15 new tests in Phase 5):
  - `tests/unit/test_extractor.py` (4 tests): Multi-page PDF page numbers, blank page handling, block bounding boxes, corrupt payload handling.
  - `tests/unit/test_normalizer.py` (6 tests): Decimal dosage preservation (`0.5 mg`, `.25 mcg`, `12.5 mg/dL`), medical units (`mL/min/1.73m²`, `mmHg`), Latin abbreviations (`b.i.d.`, `p.r.n.`, `q.h.s.`), de-hyphenation across line breaks, clinical hyphen preservation (`EGFR-mutated`, `COVID-19`), Unicode whitespace cleanup.
  - `tests/unit/test_chunker.py` (3 tests): 100% page-number retention across multi-page document, context header injection format, sentence boundary preservation for decimals and abbreviations.
  - `tests/integration/test_ingestion.py` (2 tests): End-to-end ingestion pipeline (upload PDF -> trigger ingest -> retrieve chunks with exact page provenance -> idempotent re-ingestion), cross-patient RBAC isolation enforcement (403 Forbidden).
- [x] **6. Static Checks Passing:**
  - Python: `ruff check backend tests` passed with 0 errors.
  - Python: `mypy backend` passed with 0 errors across 42 source files.
  - Frontend: `npm run build` (`tsc && vite build`) produced production bundle in 2.99s with 0 errors.
- [x] **7. Security & Isolation Enforced:** Document ingestion and chunk retrieval strictly enforce patient-level authorization (`get_document`). Unauthorized users receive `403 Forbidden`.
- [x] **8. Error Handling & Edge Cases:** Empty or corrupted PDFs handled gracefully; re-ingestion cleanly purges previous chunks idempotently; failure states set `ingestion_status = "failed"` with captured `error_message`.
- [x] **9. Audit Trail Active:** Append-only audit logger writes `DOCUMENT_INGESTED` events with chunk counts, total tokens, and page counts.
- [x] **10. Frontend Workspace Integrated:**
  - `DocumentList.tsx`: Added "Parse PDF" button for pending/failed documents with interactive loading state.
  - Added "Chunks" provenance button for completed documents.
  - Built interactive `ChunkInspectorModal.tsx` showing chunk cards, physical page filters, token counts, and highlighted context headers.
- [x] **11. Known Limitations Recorded:** Vector embedding and Qdrant indexing are deferred to Phase 6; chunks are currently persisted in SQLite/PostgreSQL `document_chunks` table with provenance metadata.
- [x] **12. Phase Tracker Updated:** Phase 5 marked Verified and Approved.
- [x] **13. Explicit User Approval Requested:** Phase 5 reviewed and approved by user.

---

## 7. Phase 6 Verification Checklist (Definition of Done)

- [x] **1. Requirements & Scope Documented:** Dense vector embedding provider using FastEmbed (`BAAI/bge-small-en-v1.5`, 384 dimensions, CPU ONNX) and Qdrant collection indexing with payload isolation filtering aligned with FR-RET-01, FR-RET-02, and RAG_DESIGN requirements.
- [x] **2. Modular Architecture Enforced:**
  - Embedding Provider: `backend/vector/embeddings.py` (`FastEmbedProvider`, `get_embedding_provider`, 384-dim, lazy loading, L2 normalized).
  - Qdrant Vector Store: `backend/vector/store.py` (`QdrantVectorStore`, `get_vector_store`, collection `patient360_chunks`, Cosine distance, HNSW `m=16`, `ef_construct=100`, auto-fallback `:memory:` embedded mode).
  - Ingestion Hook: `backend/ingestion/service.py` (`index_document_chunks_in_qdrant` hook with idempotent pre-cleanup).
  - Schemas: `backend/schemas/vector.py` (`VectorSearchRequest`, `VectorSearchResultItem`, `VectorStatsResponse`).
  - API Routes: `GET /api/v1/vector/stats`, `POST /api/v1/vector/search` (enforcing server-side patient-level access boundary).
  - Health Probe: `backend/api/v1/health.py` reports vector store status for both daemon and in-memory modes.
- [x] **3. No Secrets / Real PHI Committed:** All embedded payloads use synthetic clinical cases (`SYN-VEC-01`, `Eleanor Vance`); zero real PHI stored; Qdrant payloads contain only synthetic clinical chunks.
- [x] **4. Dependencies Documented:** `fastembed>=0.3.0` and `qdrant-client>=1.9.0` verified in `.venv` environment and `requirements.txt`.
- [x] **5. Automated Tests Passing:** **56/56 pytest tests pass** (8 new comprehensive tests in Phase 6):
  - `tests/unit/test_embeddings.py` (3 tests): Model output dimensionality (384 float32), non-zero unit vectors, batch embedding throughput and consistency.
  - `tests/unit/test_vector_store.py` (3 tests): Collection initialization, chunk upsert and retrieval, patient isolation payload filtering, document chunk deletion.
  - `tests/integration/test_vector_indexing.py` (2 tests): End-to-end ingestion pipeline vector indexing and semantic search; cross-patient security boundary rejection (`403 Forbidden`).
- [x] **6. Static Checks Passing:**
  - Python: `ruff check backend tests` passed with 0 errors.
  - Python: `mypy backend tests` passed with 0 errors across 63 source files.
  - Frontend: `npm run build` (`tsc && vite build`) produced production bundle in 4.16s with 0 errors.
- [x] **7. Security & Isolation Enforced:** `POST /api/v1/vector/search` strictly verifies caller access to the requested patient dossier before querying Qdrant. Qdrant searches apply server-side payload filters (`patient_id == ...`), preventing cross-patient vector leakage even if a query is identical.
- [x] **8. Error Handling & Edge Cases:** Embedded `:memory:` fallback seamlessly activates when standalone Qdrant server is absent; empty query validation; idempotent re-indexing prevents duplicate vectors; batch embedding handles single and multi-chunk inputs safely.
- [x] **9. Audit Trail Active:** Ingestion audit logs record chunk and vector indexing counts; search access logged when unauthorized access is attempted.
- [x] **10. Frontend Workspace Integrated:**
  - `frontend/src/features/documents/SemanticSearchModal.tsx`: Interactive modal with prompt presets, top-K selector, real-time cosine score badges, page badges, and context header view.
  - `frontend/src/features/documents/DocumentList.tsx`: Added "Semantic Search" action button to patient dossier header.
  - `frontend/src/App.tsx`: Updated `PHASES_DATA` marking Phase 6 as "Verified".
- [x] **11. Known Limitations Recorded:** BM25 sparse search and reciprocal rank fusion (RRF) are scheduled for Phase 8; LLM synthesis over retrieved vector chunks is scheduled for Phase 7.
- [x] **12. Phase Tracker Updated:** Phase 6 marked Verified and Approved.
- [x] **13. Explicit User Approval Requested:** Phase 6 reviewed and approved by user.

---

## 8. Phase 7 Verification Checklist (Definition of Done)

- [x] **1. Requirements & Scope Documented:** Evidence-grounded clinical question-answering with dense vector retrieval, context token budget management, anti-injection passage boundaries, LLM generation adapter, citation verification, and deterministic abstention aligned with FR-RET-01..05, FR-RAG-01..04, and RAG_DESIGN.
- [x] **2. Modular Architecture Enforced:**
  - LLM Interface: `backend/rag/llm.py` (`BaseLLMProvider`, `MockLLMProvider`, `get_llm_provider`, `LLMResponse`).
  - Context & Prompt Builder: `backend/rag/prompt.py` (`GroundedPromptBuilder`, `CLINICAL_SYSTEM_PROMPT`, untrusted delimiter enclosures `<<<UNTRUSTED_DOCUMENT_CONTENT [Doc: ..., Page: ...]>>>`).
  - Citation Engine: `backend/rag/citations.py` (`CitationVerifier`, exact claim-to-passage quote resolution, `supported`/`partially_supported`/`unsupported` status assignment, abstention detection).
  - Orchestrator Service: `backend/rag/service.py` (`RAGService`, `get_rag_service`, confidence score calculation, limitations detection, performance telemetry).
  - Schemas: `backend/schemas/rag.py` (`RAGQueryRequest`, `RAGQueryResponse`, `CitationItem`, `RetrievalMetadata`, `RAGFeedbackRequest`, `RAGFeedbackResponse`).
  - API Routes: `backend/api/v1/rag.py` (`POST /query`, `POST /feedback`).
- [x] **3. No Secrets / Real PHI Committed:** All clinical prompts and test fixtures use synthetic patients (`SYN-RAG-01`, `Eleanor Vance`); zero real PHI stored; API keys kept in environment variables with safe offline `MockLLMProvider` fallback.
- [x] **4. Dependencies Documented:** FastEmbed, PyMuPDF, Qdrant-Client, Pydantic, and FastAPI verified without requiring external cloud API keys or heavy GPU runtimes for standard operation.
- [x] **5. Automated Tests Passing:** **67/67 pytest tests pass** (11 new comprehensive tests in Phase 7):
  - `tests/unit/test_rag_prompt.py` (2 tests): Prompt delimiter injection, untrusted document boundaries, and context token budget truncation.
  - `tests/unit/test_rag_citations.py` (3 tests): Citation extraction, exact quote resolution, unsupported/hallucinated citation detection, and abstention phrase recognition.
  - `tests/unit/test_rag_llm.py` (2 tests): Grounded answer generation with page citations, deterministic abstention on unmentioned clinical inquiries.
  - `tests/integration/test_rag_pipeline.py` (4 tests): End-to-end ingestion and grounded RAG query (with page 2 citation and supported status); deterministic abstention on unmentioned facts (`is_abstention=True`); cross-patient access boundary rejection (`403 Forbidden`); clinician feedback submission (`201 Created`).
- [x] **6. Static Checks Passing:**
  - Python: `ruff check backend tests` passed with 0 errors.
  - Python: `mypy backend tests` passed with 0 errors across 74 source files.
  - Frontend: `npm run build` (`tsc && vite build`) produced production bundle in 5.58s with 0 errors.
- [x] **7. Security & Isolation Enforced:** `POST /api/v1/rag/query` and `POST /api/v1/rag/feedback` strictly enforce tenant/patient authorization (`check_user_patient_access`). Non-permitted users receive `403 Forbidden`. Document passages are isolated within untrusted content delimiters to neutralize prompt injection.
- [x] **8. Error Handling & Edge Cases:** Zero retrieved chunks gracefully return clean abstention without crashing; ungrounded inquiries trigger standard clinical abstention (`"Insufficient evidence documented in available records."`); token overflow handled safely via budget truncation.
- [x] **9. Audit Trail Active:** Append-only audit logging records `RAG_QUERY_EXECUTED` (with query length, candidate count, citation count, abstention flag, confidence score) and `RAG_FEEDBACK_SUBMITTED` (with rating, issue type, comment).
- [x] **10. Frontend Workspace Integrated:**
  - `frontend/src/features/rag/ClinicalRAGPanel.tsx`: Interactive clinical Q&A drawer with quick suggestion pills, confidence score gauge, verified citation cards, exact source excerpt inspector, limitations caveats, and clinician rating modal.
  - `frontend/src/App.tsx`: Added seamless tab switcher (`Attached Documents` vs `Grounded Clinical RAG`) in patient dossier workspace; marked Phase 7 as `Verified` in `PHASES_DATA`.
- [x] **11. Known Limitations Recorded:** BM25 sparse search and Reciprocal Rank Fusion (RRF) are scheduled for Phase 8; PDF in-viewer highlight navigation is scheduled for Phase 8.
- [x] **12. Phase Tracker Updated:** Phase 7 marked Completed (Pending Approval).
- [x] **13. Explicit User Approval Requested:** Awaiting user review before Phase 8.

---

## 9. Active Risks & Outstanding Issues
* **Hybrid Retrieval:** Current retrieval uses dense vector search (FastEmbed 384-d). Exact clinical keywords (e.g. rare drug abbreviations or exact numeric codes) will benefit from BM25 sparse retrieval.
* **Next Action:** Phase 8 will implement Advanced Hybrid RAG (In-memory BM25 sparse indexer, Reciprocal Rank Fusion merger with $k=60$, and interactive PDF viewer with clickable citations).
