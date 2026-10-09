# Patient360: Project Status and Phase Tracker

## 1. Master Phase Tracker

| Phase | Phase Name | Status | Prerequisites | Key Deliverables | Verification Evidence | Approval Status |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| **1** | **Discovery, Requirements & Architecture** | **In Progress** | Empty workspace | 15 docs in `docs/`, architecture diagrams, data models | Phase 1 document review completed | Pending Approval |
| **2** | Development Foundation & Tooling Setup | Planned | Phase 1 | Docker compose, FastAPI skeleton, React/Vite, health probes | Pending Phase 2 | Planned |
| **3** | Authentication, Authorization & RBAC | Planned | Phase 2 | JWT auth, Argon2, RBAC guards, user tables | Pending Phase 3 | Planned |
| **4** | Patient & Document Management | Planned | Phase 3 | Patient CRUD, PDF upload, storage adapter, isolation | Pending Phase 4 | Planned |
| **5** | Document Ingestion, Parsing & Chunking | Planned | Phase 4 | PyMuPDF extractor, normalizer, semantic chunker | Pending Phase 5 | Planned |
| **6** | Embeddings & Vector Indexing | Planned | Phase 5 | FastEmbed CPU adapter, Qdrant collection, payload filters | Pending Phase 6 | Planned |
| **7** | Baseline Grounded RAG | Planned | Phase 6 | LLM adapter, grounded prompt builder, citation parser | Pending Phase 7 | Planned |
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

- [x] **1. Requirements & Scope Documented:** Defined in `docs/PROJECT_CHARTER.md` and `docs/REQUIREMENTS.md`.
- [x] **2. Modular Architecture Defined:** Detailed in `docs/ARCHITECTURE.md` with sequence & component diagrams.
- [x] **3. No Secrets / Real PHI Committed:** Verified zero credentials; all schemas use synthetic identifiers.
- [x] **4. Dependencies Documented:** FastEmbed, PyMuPDF, Qdrant, PostgreSQL, FastAPI, React/Vite/TS justified in `docs/DECISIONS.md`.
- [x] **5. Database Schema & Data Models Defined:** Complete PostgreSQL DDL and Qdrant payload schema in `docs/DATA_MODEL.md`.
- [x] **6. API Contracts Specified:** Complete OpenAPI endpoint schemas in `docs/API_SPECIFICATION.md`.
- [x] **7. Security & Threat Model Analyzed:** STRIDE model and prompt injection mitigations in `docs/THREAT_MODEL.md`.
- [x] **8. Healthcare Safety & Privacy Specified:** Disclaimers, abstention rules, and de-identification in `docs/PRIVACY_AND_SAFETY.md`.
- [x] **9. RAG & Retrieval Engine Designed:** Hybrid RRF and citation verifier documented in `docs/RAG_DESIGN.md`.
- [x] **10. Evaluation & Benchmarking Planned:** 50-item synthetic benchmark and metric targets in `docs/EVALUATION_PLAN.md`.
- [x] **11. Test Strategy Formalized:** Multi-tier automated testing pyramid specified in `docs/TEST_STRATEGY.md`.
- [x] **12. Deployment & Resource Limits Planned:** Windows CPU setup and container memory limits in `docs/DEPLOYMENT.md`.
- [x] **13. Explicit User Approval Requested:** Awaiting user review and sign-off on Phase 1 deliverables.

---

## 3. Active Risks & Outstanding Issues
* **Active Risk:** External LLM Provider choice. *Status:* Defaulting to Google Gemini API adapter with Mock fallback for automated CI tests.
* **Active Risk:** Windows Docker WSL2 startup latency. *Status:* Container resource limits enforced (512M) to avoid host starvation.
