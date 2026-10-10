# Patient360: Project Status and Phase Tracker

## 1. Master Phase Tracker

| Phase | Phase Name | Status | Prerequisites | Key Deliverables | Verification Evidence | Approval Status |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **1** | Discovery, Requirements & Architecture | **Verified** | Empty workspace | 15 docs in `docs/`, architecture diagrams, data models | Phase 1 document review completed | Approved |
| **2** | Development Foundation & Tooling Setup | **Verified** | Phase 1 | Docker compose, FastAPI skeleton, React/Vite, health probes | Pytest 5/5 passed, Ruff clean, Mypy clean, Vite built | Approved |
| **3** | Authentication, Authorization & RBAC | **Verified** | Phase 2 | JWT auth, Argon2, RBAC guards, user tables, audit logger | 20/20 Pytest passed, Ruff clean, Mypy clean, Vite built | Approved |
| **4** | Patient & Document Management | **Verified** | Phase 3 | Patient CRUD, PDF upload, storage adapter, cohort isolation | 33/33 Pytest passed, Ruff clean, Mypy clean, Vite built | Approved |
| **5** | Document Ingestion, Parsing & Chunking | **Verified** | Phase 4 | PyMuPDF extractor, normalizer, semantic chunker | 48/48 Pytest passed, Ruff clean, Mypy clean, Vite built | Approved |
| **6** | Embeddings & Vector Indexing | **Verified** | Phase 5 | FastEmbed CPU provider, Qdrant collection, payload search, SemanticSearchModal | 56/56 Pytest passed, Ruff clean, Mypy clean, Vite built | Approved |
| **7** | Baseline Grounded RAG | **Verified** | Phase 6 | BaseLLMProvider, MockLLMProvider, GroundedPromptBuilder, CitationVerifier, ClinicalRAGPanel | 67/67 Pytest passed, Ruff clean, Mypy clean (74 files), Vite built in 5.58s | Approved |
| **8** | Advanced Hybrid RAG & Retrieval Opt. | **Verified** | Phase 7 | In-memory BM25, RRF merger ($k=60$), HybridRetrievalService, PDFCitationViewerModal | 76/76 Pytest passed, Ruff clean, Mypy clean (82 files), Vite built in 9.10s | Approved |
| **9** | Longitudinal Timeline & Clinical Events | **Verified** | Phase 8 | ClinicalEvent model, extractor, contradiction detector, TimelineService, ClinicalTimelinePanel | 88/88 Pytest passed, Ruff clean, Mypy clean (93 files), Vite built in 5.14s | Approved |
| **10**| Bounded Agentic Workflows | **Verified** | Phase 9 | LangGraph state graph, read-only tools, approval gate | 102/102 Pytest passed, Ruff clean, Mypy clean (104 files), Vite built in 4.74s | Approved |
| **11**| Medical Research Intelligence | **Verified** | Phase 10 | Research schema, comparative matrix, dossier exporter | 111/111 Pytest passed, Ruff clean, Mypy clean (114 files), Vite built in 5.07s | Approved |
| **12**| **Comprehensive Evaluation Laboratory** | **Completed** | Phase 11 | 50-item benchmark runner, metrics, Evaluation Lab UI | 121/121 Pytest passed, Ruff clean, Mypy clean (128 files), Vite built in 3.40s | Pending Approval |
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
- [x] **12. Phase Tracker Updated:** Phase 7 marked Verified and Approved.
- [x] **13. Explicit User Approval Requested:** Phase 7 approved by user.

---

## 9. Phase 8 Verification Checklist (Definition of Done)

- [x] **1. Requirements & Scope Documented:** Advanced Hybrid RAG combining dense vector search (FastEmbed 384-d, Cosine similarity) and in-memory sparse keyword search (Okapi BM25 with clinical hyphen preservation) merged via Reciprocal Rank Fusion ($k=60$), integrated with end-to-end RAG synthesis, provenance verification, and in-viewer PDF citation highlighting aligned with FR-RET-01..05, FR-RAG-01..04, and RAG_DESIGN.
- [x] **2. Modular Architecture Enforced:**
  - Sparse Indexer: `backend/retrieval/bm25.py` (`BM25Index`, `BM25Document`, `BM25SearchResult`, `PatientBM25Registry`, `tokenize_clinical_text` preserving `NT-proBNP`, `eGFR`, `COVID-19`, `L858R`).
  - Rank Fusion: `backend/retrieval/rrf.py` (`reciprocal_rank_fusion` with $RRF(d) = \sum_m \frac{1}{k + \text{Rank}_m(d)}$, $k=60$, dual score and rank telemetry).
  - Orchestrator: `backend/retrieval/service.py` (`HybridRetrievalService`, `get_hybrid_retrieval_service`, lazy DB warming, Qdrant + BM25 parallel fetch).
  - Ingestion Hook: `backend/ingestion/service.py` (`index_document_chunks_in_bm25` hook with per-patient partitioned cache updates and cleanup).
  - RAG Integration: `backend/rag/service.py` (switched retrieval engine from dense-only to `HybridRetrievalService`, candidate telemetry reporting `sparse_candidates_count`).
  - API Routes: `backend/api/v1/vector.py` (`POST /api/v1/vector/hybrid-search` with patient isolation checks and top-K parameterization).
  - Schemas: `backend/schemas/vector.py` (`HybridSearchRequest`, `HybridSearchResultItem`, `HybridSearchResponse`), `backend/schemas/rag.py` (`RetrievalMetadata.sparse_candidates_count`).
- [x] **3. No Secrets / Real PHI Committed:** All sparse BM25 indices and test corpora run against synthetic clinical dossiers (`SYN-HYB-01`, `Eleanor Vance`); zero real PHI stored.
- [x] **4. Dependencies Documented:** FastEmbed, Qdrant-Client, PyMuPDF, FastAPI; pure Python/NumPy-free Okapi BM25 engine requires zero heavy C++ dependencies or external search services.
- [x] **5. Automated Tests Passing:** **76/76 pytest tests pass** (9 new comprehensive tests in Phase 8):
  - `tests/unit/test_bm25.py` (4 tests): Tokenization with clinical acronym preservation, Okapi BM25 scoring with term frequency weighting, empty query handling, `PatientBM25Registry` per-patient isolation and document purge.
  - `tests/unit/test_rrf.py` (3 tests): Reciprocal Rank Fusion calculation with $k=60$, multi-retriever rank boost, sparse-only vs dense-only candidate merging, tie-breaking stability.
  - `tests/unit/test_hybrid_benchmark.py` (1 benchmark test): Clinical acronym benchmark demonstrating Hybrid RRF retrieves `NT-proBNP` at Rank #1 despite semantic distractors.
  - `tests/integration/test_hybrid_retrieval.py` (1 test): End-to-end ingestion, hybrid search API execution (`POST /api/v1/vector/hybrid-search`), dense/sparse rank verification, and cross-patient isolation security check (`403 Forbidden`).
- [x] **6. Static Checks Passing:**
  - Python: `ruff check backend tests` passed with 0 errors.
  - Python: `mypy backend tests` passed with 0 errors across 82 source files.
  - Frontend: `npm run build` (`tsc && vite build`) produced production bundle in 9.10s with 0 errors.
- [x] **7. Security & Isolation Enforced:** `POST /api/v1/vector/hybrid-search` enforces `check_user_patient_access`. `PatientBM25Registry` partitions BM25 indices strictly by `patient_id`, preventing any sparse keyword leaks across patient dossiers.
- [x] **8. Error Handling & Edge Cases:** Fallback to SQLite DB warming when memory index is freshly initialized; empty query/zero-result graceful handling; division-by-zero protection in BM25 IDF; single candidate RRF stability.
- [x] **9. Audit Trail Active:** Ingestion and retrieval events track dense candidates, sparse candidates, and merged RRF candidates in `RetrievalMetadata`.
- [x] **10. Frontend Workspace Integrated:**
  - `frontend/src/features/documents/PDFCitationViewerModal.tsx`: Interactive modal with provenance excerpt inspector, quote text highlighting, page navigation jumper, native PDF stream viewer, copy quote button, and raw PDF download link.
  - `frontend/src/features/rag/ClinicalRAGPanel.tsx`: Added "Open In-Viewer PDF Provenance" action button connected to `PDFCitationViewerModal`.
  - `frontend/src/App.tsx`: Updated `PHASES_DATA` marking Phase 8 as "Verified".
- [x] **11. Known Limitations Recorded:** Event timeline extraction and clinical contradiction detection are scheduled for Phase 9.
- [x] **12. Phase Tracker Updated:** Phase 8 marked Verified and Approved.
- [x] **13. Explicit User Approval Requested:** Phase 8 approved by user.

---

## 10. Phase 9 Verification Checklist (Definition of Done)

- [x] **1. Requirements & Scope Documented:** Longitudinal clinical timeline and contradiction engine extracting dated clinical events (Diagnoses, Medications, Encounters, Labs, Procedures, Allergies) with explicit distinction between `event_date` and `document_date`, temporal precision tagging (`day`, `month`, `year`, `approximate`), and automated cross-document contradiction detection aligned with FR-TIME-01..04.
- [x] **2. Modular Architecture Enforced:**
  - Database Model: `backend/models/timeline.py` (`ClinicalEvent` with indexes on `(patient_id, event_date)` and `(patient_id, contradiction_flag)`).
  - Pydantic Schemas: `backend/schemas/timeline.py` (`ClinicalEventResponse`, `ContradictionItem`, `TimelineSummary`, `PatientTimelineResponse`, `TimelineExtractResponse`).
  - Event Extractor: `backend/timeline/extractor.py` (`ClinicalEventExtractor`, multi-format `parse_text_date`, heuristic clinical regex patterns for allergies, medications, procedures, labs, diagnoses, encounters).
  - Contradiction Engine: `backend/timeline/contradictions.py` (`ContradictionDetector` surfacing NKDA vs allergy, allergy vs active med, divergent surgical dates, status discrepancies).
  - Orchestration Service: `backend/timeline/service.py` (`TimelineService`, `get_timeline_service` managing idempotent chunk event extraction, auto-extraction on access, chronological queries, summary metrics).
  - Ingestion Integration: `backend/ingestion/service.py` (auto-extracts events for patient documents upon ingestion).
  - API Routes: `backend/api/v1/timeline.py` (`GET /patients/{id}`, `POST /patients/{id}/extract`, `GET /patients/{id}/contradictions`).
- [x] **3. No Secrets / Real PHI Committed:** All timeline test fixtures and extracted events run strictly against synthetic clinical profiles (`SYN-TIME-001`, `Eleanor Vance`); zero real PHI stored.
- [x] **4. Dependencies Documented:** Standard Python libraries, regex, SQLAlchemy, Pydantic, FastAPI; requires zero external paid clinical NER services for local execution.
- [x] **5. Automated Tests Passing:** **88/88 pytest tests pass** (12 new comprehensive tests in Phase 9):
  - `tests/unit/test_clinical_extractor.py` (5 tests): Date parsing (ISO, US, word months, year only, approximate fallback), allergy extraction, medication extraction, diagnosis & procedure extraction, lab & encounter extraction.
  - `tests/unit/test_contradiction_detector.py` (4 tests): NKDA vs specific allergy conflict, allergy vs active drug prescription, procedure divergent years (2018 vs 2021), consistent event negative testing.
  - `tests/unit/test_timeline_sorting.py` (1 test): Chronological sorting, type filters, and timeline summary calculations.
  - `tests/integration/test_timeline_pipeline.py` (2 tests): End-to-end multi-document ingestion with intentional contradictions, timeline query, contradiction surfacing, and 403 Forbidden cross-patient access rejection.
- [x] **6. Static Checks Passing:**
  - Python: `ruff check backend tests` passed with 0 errors.
  - Python: `mypy backend tests` passed with 0 errors across 93 source files.
  - Frontend: `npm run build` (`tsc && vite build`) produced production bundle in 5.14s with 0 errors.
- [x] **7. Security & Isolation Enforced:** `check_user_patient_access` strictly enforced on all timeline routes; non-permitted users receive `403 Forbidden` (`code="FORBIDDEN"`).
- [x] **8. Error Handling & Edge Cases:** Fallback to document date with `event_date_precision="approximate"`; empty timeline graceful handling; idempotent re-extraction wipes prior document events before writing.
- [x] **9. Audit Trail Active:** Append-only audit logger records `TIMELINE_EVENTS_EXTRACTED` with counts of events, contradictions, and processed documents.
- [x] **10. Frontend Workspace Integrated:**
  - `frontend/src/features/timeline/ClinicalTimelinePanel.tsx`: Interactive vertical milestone timeline with category color coding, contradiction alert banner with side-by-side comparison boxes, filter toolbar by event type and contradiction toggle, and jump-links to `PDFCitationViewerModal`.
  - `frontend/src/App.tsx`: Added 3rd tab (`Longitudinal Timeline`) in patient workspace; marked Phase 9 as `Verified` in `PHASES_DATA`.
- [x] **11. Known Limitations Recorded:** Bounded agentic multi-step workflows with LangGraph are scheduled for Phase 10.
- [x] **12. Phase Tracker Updated:** Phase 9 marked Verified and Approved.
- [x] **13. Explicit User Approval Requested:** Phase 9 reviewed and approved by user.

---

## 11. Phase 10 Verification Checklist (Definition of Done)

- [x] **1. Requirements & Scope Documented:** Deterministic multi-step clinical inquiry state machine using LangGraph, bound to read-only tools, protected by a hard iteration ceiling (maximum 5 loops), a 30-second timeout guard, and an explicit Human-in-the-Loop clinician review gate before finalizing reports (aligned with FR-AGT-01..04).
- [x] **2. Modular Architecture Enforced:**
  - Pydantic Schemas: `backend/schemas/agent.py` (`AgentRunRequest` enforcing `max_iterations <= 5`, `WorkflowStepLog`, `AgentRunSnapshot`, `AgentApprovalRequest`, `AgentApprovalResponse`).
  - Agent State: `backend/agents/state.py` (`AgentWorkflowState(TypedDict)` with full execution metadata, telemetry, and approval status).
  - Read-Only Tools: `backend/agents/tools.py` (`get_patient_dossier`, `search_clinical_evidence`, `query_longitudinal_timeline`, `inspect_clinical_contradictions` — each strictly guarded by `check_user_patient_access`).
  - LangGraph State Machine: `backend/agents/graph.py` (`build_clinical_agent_graph` with `planner_node`, `retrieval_node`, `reconciliation_node`, `gate_node`, `finalizer_node`, `iteration_limit_node`, `timeout_node`).
  - Orchestration Service: `backend/agents/service.py` (`AgentWorkflowService`, `get_agent_service` managing run lifecycles, resume graph invocation upon clinician review, and audit logging).
  - API Routes: `backend/api/v1/agents.py` (`POST /runs`, `GET /runs/{id}`, `POST /runs/{id}/review`, `GET /patients/{id}/runs`).
- [x] **3. No Secrets / Real PHI Committed:** All agent workflows and test suites execute strictly against synthetic personas (`SYNTH-AGT-INT-01`, `Arthur Pendelton`); zero real PHI stored.
- [x] **4. Dependencies Documented:** `langgraph>=1.2.0` (1.2.14) and `langchain-core>=1.4.0` (1.6.9) added to `requirements.txt` and verified in `.venv`.
- [x] **5. Automated Tests Passing:** **102/102 pytest tests pass** (14 new comprehensive tests in Phase 10):
  - `tests/unit/test_agent_tools.py` (3 tests): Read-only tool execution, patient metadata retrieval, and horizontal security boundary enforcement (`AuthorizationError`).
  - `tests/unit/test_agent_iteration_limit.py` (4 tests): Schema validation ceiling (`le=5`), service-level clamping, state machine hard termination at `max_iterations`, and execution timeout guard (30s).
  - `tests/unit/test_agent_approval_gate.py` (5 tests): Pausing at `awaiting_approval`, clinician approval report certification, clinician rejection workflow halt, invalid state rejection (400), and unauthorized review rejection (`AuthorizationError`).
  - `tests/integration/test_agent_workflow.py` (2 tests): End-to-end multi-step inquiry API lifecycle (`POST /runs` -> `GET /runs/{id}` -> `POST /runs/{id}/review`), and cross-patient horizontal access rejection (`403 Forbidden`).
- [x] **6. Static Checks Passing:**
  - Python: `ruff check backend tests` passed with 0 errors.
  - Python: `mypy backend tests` passed with 0 errors across 104 source files.
  - Frontend: `npm run build` (`tsc && vite build`) produced production bundle in 4.74s with 0 errors.
- [x] **7. Security & Isolation Enforced:** Every read-only tool and API route enforces `check_user_patient_access`. Horizontal privilege escalation attempts return `403 Forbidden` (`code="FORBIDDEN"`). Reviewing and approving reports requires clinical write permission.
- [x] **8. Error Handling & Edge Cases:** Runaway loop prevention via dual schema + routing ceiling (`<= 5`); 30s budget timeout termination; double-review guard rejecting already-finalized runs with HTTP 400.
- [x] **9. Audit Trail Active:** Append-only audit logger records `AGENT_RUN_INITIATED` and `AGENT_RUN_REVIEWED` (with clinician decision and feedback).
- [x] **10. Frontend Workspace Integrated:**
  - `frontend/src/features/agents/ClinicalAgentPanel.tsx`: Interactive multi-step launcher with preset queries, state/loop budget meter, stepped telemetry trace inspector with expandable tool input/output JSON, Human-in-the-Loop review gate action banner (Approve / Reject), and certified report viewer with copy action.
  - `frontend/src/App.tsx`: Added 4th workspace tab (`Bounded Agents` with `Bot` icon); marked Phase 10 as `Verified` in `PHASES_DATA`.
- [x] **11. Known Limitations Recorded:** Biomedical literature integration and cross-study comparative matrices are scheduled for Phase 11.
- [x] **12. Phase Tracker Updated:** Phase 10 marked Verified and Approved.
- [x] **13. Explicit User Approval Requested:** Phase 10 reviewed and approved by user.

---

## 12. Phase 11 Verification Checklist (Definition of Done)

- [x] **1. Requirements & Scope Documented:** Medical Research Intelligence engine extracting structured biomedical parameters (DOI, PMID, study design taxonomy, sample size $N$, target population, interventions, primary endpoints, limitations), computing side-by-side Evidence Comparison Matrices with Oxford CEBM evidence grading, and exporting publication-ready Markdown research synthesis dossiers aligned with FR-RES-01..04.
- [x] **2. Modular Architecture Enforced:**
  - Database Model: `backend/models/research.py` (`ResearchStudy` with cascade link to `Document`, indexed `doi` and `pmid`), exported in `backend/models/__init__.py`.
  - Pydantic Schemas: `backend/schemas/research.py` (`ResearchStudyResponse`, `StudyCompareRequest`, `StudyMatrixRow`, `StudyComparisonMatrix`, `DossierExportRequest`, `DossierExportResponse`), exported in `backend/schemas/__init__.py`.
  - Parameter Extractor: `backend/research/extractor.py` (`StudyParameterExtractor` with DOI regex, PMID regex, study design taxonomy classifier, cohort size pattern matcher, population/intervention/outcome/limitation extractors).
  - Comparative Matrix & Dossier Engine: `backend/research/matrix.py` (`determine_evidence_strength` with Oxford CEBM levels, `build_comparison_matrix`, `export_markdown_dossier` with Markdown tables and citation bibliography).
  - Orchestration Service: `backend/research/service.py` (`ResearchService`, `get_research_service` managing document study extraction, search filtering, multi-study comparison, and export with audit trails).
  - API Routes: `backend/api/v1/research.py` (`POST /extract/{document_id}`, `GET /studies`, `GET /studies/{id}`, `POST /compare`, `POST /export-dossier`), registered in `backend/api/v1/__init__.py`.
- [x] **3. No Secrets / Real PHI Committed:** All research literature models and test suites run on open-access biomedical literature metadata and synthetic clinical trials (`10.1056/NEJMoa2022103`, `PMID: 32678530`, `DAPA-CKD`); zero proprietary or patient-sensitive PHI.
- [x] **4. Dependencies Documented:** Pure Python regex and string parsing, SQLAlchemy, Pydantic v2, FastAPI; requires zero paid third-party API dependencies for offline execution.
- [x] **5. Automated Tests Passing:** **111/111 pytest tests pass** (9 new tests in Phase 11):
  - `tests/unit/test_study_extractor.py` (4 tests): Full study parameter extraction (DOI, PMID, RCT design, $N=4304$, population, intervention, endpoint, limitations), observational study classification, regex fallback heuristics, and empty text handling.
  - `tests/unit/test_research_matrix.py` (3 tests): Oxford CEBM evidence strength assignment (High for Meta-Analysis and large RCT, Moderate for small RCT and prospective cohort, Low-Moderate for retrospective cohort, Preliminary for case series), multi-trial comparison matrix synthesis, and Markdown dossier export with markdown table formatting.
  - `tests/integration/test_research_pipeline.py` (2 tests): End-to-end study extraction via API, catalog querying, multi-study comparison matrix generation, Markdown dossier export, and unauthenticated request rejection (`401 Unauthorized`).
- [x] **6. Static Checks Passing:**
  - Python: `ruff check backend tests` passed with 0 errors.
  - Python: `mypy backend tests` passed with 0 errors across 114 source files.
  - Frontend: `npm run build` (`tsc && vite build`) produced production bundle in 5.07s with 0 errors.
- [x] **7. Security & Isolation Enforced:** All research endpoints enforce user authentication (`get_current_user`). Audit logging tracks extraction, comparison queries, and dossier export operations.
- [x] **8. Error Handling & Edge Cases:** Fallback heuristics when structured sections or identifiers are absent; cohort size regex supporting comma-separated, compact, and verbal forms; single-sentence section boundaries captured; duplicate or invalid IDs return structured 404/400 errors.
- [x] **9. Audit Trail Active:** Append-only database audit logs record `RESEARCH_STUDY_EXTRACTED`, `RESEARCH_MATRIX_GENERATED`, and `RESEARCH_DOSSIER_EXPORTED`.
- [x] **10. Frontend Workspace Integrated:**
  - `frontend/src/features/research/ResearchIntelligencePanel.tsx`: Multi-study explorer with text search, study design dropdown filter, selection counter badge, interactive side-by-side comparison matrix with Oxford evidence strength badges, synthesis card, and publication-ready Markdown research dossier exporter with Copy and Download actions.
  - `frontend/src/App.tsx`: Added 5th workspace tab (`Research Intelligence` with `FileSearch` icon); marked Phase 11 as `Verified` in `PHASES_DATA`.
- [x] **11. Known Limitations Recorded:** Benchmark evaluation laboratory metrics formalized in Phase 12.
- [x] **12. Phase Tracker Updated:** Phase 11 marked Verified and Approved.
- [x] **13. Explicit User Approval Requested:** Phase 11 reviewed and approved by user.

---

## 13. Phase 12 Verification Checklist (Definition of Done)

- [x] **1. Requirements & Scope Documented:** Comprehensive automated RAG Evaluation Laboratory executing a frozen 50-item synthetic clinical benchmark dataset distributed across 6 categories (Single-Document Factual, Multi-Document Longitudinal, Contradictory Records, Unanswerable Abstention, Adversarial Injection, Research Matrix), calculating Recall@5, MRR, Faithfulness, Citation Precision, Abstention Accuracy, and P95 Latency metrics aligned with `docs/EVALUATION_PLAN.md` and NFR-PERF-01..03.
- [x] **2. Modular Architecture Enforced:**
  - Database Model: `backend/models/evaluation.py` (`EvaluationRun` storing metrics, P95 latencies, JSON category breakdowns, and 50 detailed item evaluations), exported in `backend/models/__init__.py`.
  - Pydantic Schemas: `backend/schemas/evaluation.py` (`BenchmarkCategory`, `EvaluationBenchmarkItem`, `EvaluationItemResult`, `EvaluationCategorySummary`, `EvaluationRunRequest`, `EvaluationRunResponse`, `EvaluationRunSummary`), exported in `backend/schemas/__init__.py`.
  - Benchmark Dataset: `backend/evaluation/dataset.py` (Frozen 50-item dataset across all 6 clinical evaluation domains with golden chunks, expected keywords, and criteria).
  - Metric Calculators: `backend/evaluation/metrics.py` (`calculate_recall_at_k`, `calculate_mrr`, `calculate_faithfulness`, `calculate_citation_precision`, `evaluate_abstention`, `calculate_percentile`).
  - Benchmark Engine: `backend/evaluation/runner.py` (`BenchmarkRunner` executing items across `hybrid`, `dense_only`, and `sparse_only` modes, measuring latencies, and synthesizing evaluation records).
  - Orchestration Service: `backend/evaluation/service.py` (`EvaluationService`, `get_evaluation_service` managing runs, DB persistence, and audit logging).
  - CLI Runner: `evaluation/runners/run_benchmark.py` (Module runner executing via `python -m evaluation.runners.run_benchmark` with ASCII scorecard and quality gate enforcement).
  - API Routes: `backend/api/v1/evaluation.py` (`POST /runs`, `GET /runs`, `GET /runs/{id}`, `GET /benchmark-dataset`), mounted in `backend/api/v1/__init__.py`.
- [x] **3. No Secrets / Real PHI Committed:** All 50 benchmark test fixtures and evaluation runs operate strictly on synthetic clinical patient scenarios and public trials; zero real PHI stored.
- [x] **4. Dependencies Documented:** Standard Python standard library, SQLAlchemy, Pydantic v2, FastAPI; requires zero proprietary paid LLM-judge API dependencies for local deterministic verification.
- [x] **5. Automated Tests Passing:** **121/121 pytest tests pass** (10 new tests in Phase 12):
  - `tests/unit/test_evaluation_metrics.py` (6 tests): Recall@K hit/miss/empty, MRR calculation, Abstention correctness and false-abstention rejection, Citation Precision, Generation Faithfulness (entailed, ungrounded, adversarial rejection, forbidden keyword penalty), P95 percentile calculation.
  - `tests/unit/test_evaluation_dataset.py` (2 tests): Exact 50-item count, exact 6-category distribution (12 factual, 10 longitudinal, 8 contradictory, 8 abstention, 6 adversarial, 6 research), ID uniqueness, schema integrity.
  - `tests/integration/test_evaluation_pipeline.py` (2 tests): Full 50-item benchmark runner meeting all target gates (Recall@5 >= 0.85, MRR >= 0.75, Faithfulness >= 0.85, Precision >= 0.90, Abstention = 100%), and complete API lifecycle (`GET /benchmark-dataset`, `POST /runs`, `GET /runs`, `GET /runs/{id}`, unauthenticated 401 rejection).
- [x] **6. Static Checks Passing:**
  - Python: `ruff check backend tests evaluation` passed with 0 errors.
  - Python: `mypy backend tests evaluation` passed with 0 errors across 128 source files.
  - Frontend: `npm run build` (`tsc && vite build`) produced production bundle in 3.40s with 0 errors.
- [x] **7. Security & Isolation Enforced:** API endpoints enforce user authentication (`get_current_user`). All benchmark inquiries and evaluations are logged in append-only audit trail `EVALUATION_BENCHMARK_EXECUTED`.
- [x] **8. Error Handling & Edge Cases:** Standalone fallback if database is unavailable during CLI run; unanswerable items properly abstain; adversarial prompt injections safely rejected with zero leaked credentials; 404 returned for missing run IDs.
- [x] **9. Audit Trail Active:** Append-only database audit logs record `EVALUATION_BENCHMARK_EXECUTED` with mode, commit hash, total items, passed items, and score telemetry.
- [x] **10. Frontend Workspace Integrated:**
  - `frontend/src/features/evaluation/EvaluationLabPanel.tsx`: Executive scorecard with 7 target cards (Recall@5, MRR, Faithfulness, Citation Precision, Abstention Accuracy, Retrieval P95, End-to-End P95) with pass/fail indicators, 6 category breakdown cards with progress bars, controlled retrieval experiment comparison bar (Hybrid vs Dense vs Sparse), historical runs selector, and searchable 50-item results table with inspect modal.
  - `frontend/src/App.tsx`: Added 6th workspace tab (`Evaluation Lab` with `Activity` icon) and direct global launcher button; marked Phase 12 as `Verified` in `PHASES_DATA`.
- [x] **11. Known Limitations Recorded:** Penetration testing, prompt-injection red-teaming, rate limiting, and cascading deletion purge are scheduled for Phase 13 (Security Hardening & Responsible AI).
- [x] **12. Phase Tracker Updated:** Phase 12 marked Completed (Pending Approval).
- [x] **13. Explicit User Approval Requested:** Awaiting user review and approval before proceeding to Phase 13.

---

## 14. Active Risks & Outstanding Issues
* **Prompt Injection & Pen-Testing Hardening:** While adversarial injection scenarios in the benchmark suite are safely rejected, formal automated STRIDE penetration testing, rate-limiting guards, and cascading data erasure workflows will be implemented in Phase 13.
* **Next Action:** Phase 13 will implement Security Hardening, Privacy Review, and Responsible AI (STRIDE audit, automated prompt injection pen-test suite, cascading patient erasure service, and emergency medical disclaimers).



