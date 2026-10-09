# Patient360: System Requirements Specification

## 1. Introduction
This document defines the comprehensive Functional Requirements (FRs) and Non-Functional Requirements (NFRs) for the **Patient360** Healthcare Intelligence Platform.

---

## 2. Functional Requirements (FR)

### 2.1 Authentication & Access Control (FR-AUTH)
* **FR-AUTH-01:** The system shall authenticate users via cryptographically signed JSON Web Tokens (JWT) using Argon2 password hashing.
* **FR-AUTH-02:** The system shall enforce Role-Based Access Control (RBAC) with 4 distinct roles: `admin`, `reviewer`, `researcher`, `demo`.
* **FR-AUTH-03:** The system shall enforce patient-level authorization at the database and vector levels; users can only access patients assigned to their panel.
* **FR-AUTH-04:** The system shall reject expired, malformed, or tampered JWTs with HTTP 401 Unauthorized.

### 2.2 Document Management & Ingestion (FR-DOC)
* **FR-DOC-01:** The system shall accept PDF uploads up to 25 MB in size.
* **FR-DOC-02:** The system shall validate file magic bytes (`%PDF-`) and compute SHA-256 hashes to prevent duplicate ingestion.
* **FR-DOC-03:** The system shall extract text using PyMuPDF while preserving exact page numbers and block boundaries.
* **FR-DOC-04:** The system shall normalize text without altering clinical units (`mg/dL`, `mmHg`), decimal values (`0.5 mg`), or Latin abbreviations (`b.i.d.`, `prn`).
* **FR-DOC-05:** The system shall divide text into semantic chunks of 512 tokens with 64-token overlap, prepending document title and page headers to each chunk.
* **FR-DOC-06:** The system shall store document state (`pending`, `processing`, `completed`, `failed`) and allow idempotent reprocessing.
* **FR-DOC-07:** The system shall support cascading soft and hard deletion of documents across relational tables and vector indices.

### 2.3 Retrieval & Grounded RAG (FR-RAG)
* **FR-RAG-01:** The system shall generate 384-dimensional dense vectors using FastEmbed (`bge-small-en-v1.5`) on CPU.
* **FR-RAG-02:** The system shall index vectors in Qdrant with payload metadata filters (`patient_id`, `document_id`, `doc_type`).
* **FR-RAG-03:** The system shall maintain an in-memory BM25 index partitioned by `patient_id` for keyword matching.
* **FR-RAG-04:** The system shall execute hybrid retrieval combining dense and sparse search using Reciprocal Rank Fusion (RRF, $k=60$).
* **FR-RAG-05:** The system shall assemble context under a strict token budget (max 2,000 tokens) with untrusted data delimiter tags.
* **FR-RAG-06:** The system shall generate answers with exact bracketed citations `[Doc: {id}, Page {no}]`.
* **FR-RAG-07:** The system shall verify citations post-generation using N-gram/entailment checking against retrieved source chunks.
* **FR-RAG-08:** The system shall explicitly abstain ("Insufficient evidence documented in available records") when evidence is missing.

### 2.4 Longitudinal Timeline & Contradiction Detection (FR-TIME)
* **FR-TIME-01:** The system shall extract clinical events categorized as Diagnoses, Medications, Encounters, Labs, and Procedures.
* **FR-TIME-02:** The system shall record `event_date` independently from `document_date` and capture temporal precision (`day`, `month`, `year`, `approximate`).
* **FR-TIME-03:** The system shall detect and flag contradictory statements across multiple documents (e.g., conflicting allergy declarations or divergent surgical dates).
* **FR-TIME-04:** The system shall provide an interactive chronological timeline with event-type filtering and source jump-links.

### 2.5 Medical Research Intelligence (FR-RES)
* **FR-RES-01:** The system shall ingest biomedical research publications and extract study metadata (DOI, PMID, title, authors).
* **FR-RES-02:** The system shall extract study design, sample size, population criteria, interventions, primary endpoints, and limitations.
* **FR-RES-03:** The system shall construct structured **Evidence Comparison Matrices** contrasting multiple studies side-by-side.
* **FR-RES-04:** The system shall export cited research synthesis dossiers in Markdown format.

### 2.6 Bounded Agentic Workflows (FR-AGT)
* **FR-AGT-01:** The system shall orchestrate multi-step research inquiries via a deterministic LangGraph state machine.
* **FR-AGT-02:** The system shall bind read-only tools strictly restricted to the user's authorization scope.
* **FR-AGT-03:** The system shall enforce a hard execution ceiling of 5 iterations and a 30-second timeout per workflow.
* **FR-AGT-04:** The system shall require explicit human clinician approval before finalizing and exporting multi-source synthesized reports.

### 2.7 Security, Audit & Safety (FR-SEC)
* **FR-SEC-01:** The system shall maintain an append-only audit log recording user, timestamp, action, resource, and status.
* **FR-SEC-02:** The system shall exclude all raw clinical text and patient identifiers from log files.
* **FR-SEC-03:** The system shall display clinical safety notices and disclaimers on every generated response.
* **FR-SEC-04:** The system shall detect acute emergency symptom keywords and display emergency escalation advisories.

---

## 3. Non-Functional Requirements (NFR)

### 3.1 Performance & Latency (NFR-PERF)
* **NFR-PERF-01:** Hybrid retrieval latency (dense + BM25 + RRF) shall be $\le 1.5\text{s}$ at P95 for a patient dossier with up to 100 documents.
* **NFR-PERF-02:** End-to-end question answering latency (retrieval + LLM generation + citation verification) shall be $\le 4.0\text{s}$ at P95 when using a hosted LLM API.
* **NFR-PERF-03:** Document parsing and chunking through PyMuPDF shall process at $\ge 15\text{ pages/second}$ on standard CPU hardware.

### 3.2 Resource & Hardware Constraints (NFR-RES)
* **NFR-RES-01:** The local development stack (PostgreSQL, Qdrant, FastAPI backend, Vite frontend) shall execute on a Windows machine with 16 GB RAM and no dedicated GPU.
* **NFR-RES-02:** Docker container memory allocations shall not exceed:
  * PostgreSQL: 512 MB
  * Qdrant: 512 MB
* **NFR-RES-03:** Dense embedding generation via FastEmbed shall operate strictly on CPU using ONNX Runtime with $< 300\text{ MB}$ memory footprint.

### 3.3 Security & Privacy (NFR-SEC)
* **NFR-SEC-01:** Zero Cross-Tenant Leakage: SQL and vector queries must enforce row-level tenant/patient isolation.
* **NFR-SEC-02:** Protection against prompt injection: Documents must be treated as untrusted data wrapped in strict delimiter boundaries.
* **NFR-SEC-03:** All network traffic between frontend, backend, and external APIs shall be encrypted in transit via TLS 1.3 / HTTPS.

### 3.4 Reliability & Maintainability (NFR-REL)
* **NFR-REL-01:** The codebase shall enforce type annotations across 100% of backend Python code (Mypy strict) and frontend code (TypeScript strict).
* **NFR-REL-02:** Test coverage shall exceed $80\%$ across all backend business logic and retrieval services.
* **NFR-REL-03:** Database migrations shall be fully automated and reversible using Alembic.
* **NFR-REL-04:** The local environment shall be fully reproducible via a single Docker Compose configuration.

---

## 4. Requirements Traceability Matrix

| Requirement ID | Module / Component | Primary Phase | Verification Method |
| :--- | :--- | :--- | :--- |
| **FR-AUTH-01..04** | `backend/auth`, `backend/core/security.py` | Phase 3 | Unit & Integration Tests (pytest) |
| **FR-DOC-01..07**  | `backend/documents`, `backend/ingestion` | Phase 4, Phase 5 | Automated upload & extraction test |
| **FR-RAG-01..08**  | `backend/retrieval`, `backend/rag` | Phase 6, 7, 8 | Benchmark run & citation checks |
| **FR-TIME-01..04** | `backend/timeline` | Phase 9 | Contradiction assertion tests |
| **FR-RES-01..04**  | `backend/research` | Phase 11 | Multi-study matrix extraction test |
| **FR-AGT-01..04**  | `backend/agents` | Phase 10 | State graph execution limit test |
| **FR-SEC-01..04**  | `backend/audit`, `backend/core` | Phase 3, Phase 13 | Audit log inspection & penetration test |
| **NFR-PERF-01..03**| Core services | Phase 8, Phase 12 | Benchmark timer metrics (P95) |
| **NFR-RES-01..03** | `docker-compose.yml`, FastEmbed | Phase 2, Phase 6 | RAM inspection & Docker limits |
| **NFR-SEC-01..03** | Gateway & database filters | Phase 3, Phase 13 | Cross-patient access test |
