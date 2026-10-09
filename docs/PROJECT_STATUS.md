# Patient360: Project Status and Phase Tracker

## 1. Master Phase Tracker

| Phase | Phase Name | Status | Prerequisites | Key Deliverables | Verification Evidence | Approval Status |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| **1** | Discovery, Requirements & Architecture | **Verified** | Empty workspace | 15 docs in `docs/`, architecture diagrams, data models | Phase 1 document review completed | Approved |
| **2** | Development Foundation & Tooling Setup | **Verified** | Phase 1 | Docker compose, FastAPI skeleton, React/Vite, health probes | Pytest 5/5 passed, Ruff clean, Mypy clean, Vite built | Approved |
| **3** | **Authentication, Authorization & RBAC** | **Completed** | Phase 2 | JWT auth, Argon2, RBAC guards, user tables, audit logger | 20/20 Pytest passed, Ruff clean, Mypy clean, Vite built | Pending Approval |
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
- [x] **13. Explicit User Approval Requested:** Awaiting user review before Phase 4.

---

## 5. Active Risks & Outstanding Issues
* **Demonstration Setup:** 4 synthetic persona accounts seeded automatically with password `Patient360Secure!`.
* **Next Action:** Phase 4 will introduce Patient Dossier CRUD, PDF file validation, encrypted storage adapter, and server-side patient-level access isolation.
