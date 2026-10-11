# Patient360: Evidence-Grounded Healthcare Intelligence and Medical RAG Platform

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-teal)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue)](https://www.typescriptlang.org/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Cloud%20Run%20Ready-blue)](https://cloud.google.com/run)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20Store-red)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Docker-Production%20Hardened-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## Clinical Notice and Regulatory Disclaimer

Patient360 is an informational evidence-synthesis and document-retrieval platform developed for clinical research, medical document intelligence, and healthcare informatics workflows. It is not an FDA, CE, or national health authority cleared medical device, diagnostic system, or prescribing platform. All synthesized findings, extracted timeline events, and citations must be independently reviewed and verified by qualified healthcare professionals against primary source medical records before making clinical decisions.

---

## 1. Executive Summary and System Vision

Healthcare providers and biomedical researchers navigate highly fragmented clinical documentation spread across legacy electronic health records, consultation notes, unstructured laboratory reports, and scientific publications.

Patient360 transforms fragmented clinical documentation into structured, verifiable, and evidence-grounded intelligence.

### Core Architectural Pillars
* Hybrid Retrieval: Dense CPU-optimized semantic vectors (BAAI/bge-small-en-v1.5) combined with clinical-acronym-preserving Okapi BM25 sparse keyword search, fused via Reciprocal Rank Fusion (k=60).
* Verifiable Page Provenance: Claim-to-quote verification resolving every assertion to exact document titles, page numbers, and verbatim text, with deterministic abstention when evidence is absent.
* Longitudinal Clinical Timelines: Chronological event extraction (diagnoses, medications, procedures, labs, allergies) with automated cross-document contradiction detection.
* Bounded Agentic Workflows: Deterministic LangGraph state machine with iteration bounds (max 5), 30-second execution limits, and human-in-the-loop clinical review gates.
* Multi-Provider LLM Gateway: Provider-agnostic gateway supporting hosted Google Gemini (gemini-flash-latest, gemini-3.5-flash-lite), local offline Ollama (qwen3:4b), and an offline mock provider.
* Responsible AI Safety Framework: Real-time acute emergency symptom escalation, prompt injection defense, credential-scrubbed audit logging, and cascading patient data deletion.
* Google Cloud Ready: Production container runtime optimized for Google Cloud Run, Cloud SQL, and Secret Manager.

---

## 2. System Architecture

### Single-Block Layered Architecture Diagram

```
+=============================================================================================+
|                                    1. CLIENT & PRESENTATION TIER                            |
|  * React 18 SPA (TypeScript)      * Tailwind CSS Component Shell   * Provenance PDF Viewer   |
|  * Longitudinal Timeline View     * Cross-Study Matrix Dashboard   * Evaluation Lab Console  |
+=============================================================================================+
                                              |
                                     HTTPS / TLS 1.3 (Port 443)
                                              v
+=============================================================================================+
|                                 2. INGRESS & REVERSE PROXY TIER                             |
|  * Google Cloud Run Ingress / Nginx Proxy   * Strict Security Headers (DENY, nosniff, XSS)  |
|  * Gzip Compression & Static Caching        * Request Sanitization & Rate Limiting (SlowAPI)|
+=============================================================================================+
                                              |
                                     Internal HTTP (Port 8080)
                                              v
+=============================================================================================+
|                                3. FASTAPI BACKEND GATEWAY LAYER                             |
|  * JWT Auth & Argon2 Verification           * Role-Based Access Control (4 RBAC Roles)      |
|  * Patient Tenant Isolation Middleware      * Pydantic v2 Request / Response Validation     |
|  * Prometheus Telemetry Exposition (/metrics) * Append-Only Audit Logger with Masking Engine |
+=============================================================================================+
                                              |
                                              v
+=============================================================================================+
|                          4. DOMAIN INTELLIGENCE & ORCHESTRATION TIER                        |
|                                                                                             |
|  +---------------------------------+  +---------------------------------+                   |
|  |     HYBRID RETRIEVAL ENGINE     |  |   CLINICAL TIMELINE & CONFLICT  |                   |
|  | * Dense FastEmbed (384-d Cosine)|  | * Temporal Event Extractor      |                   |
|  | * Sparse Okapi BM25 Keyword Search| | * Event vs Document Date Split  |                   |
|  | * Reciprocal Rank Fusion (k=60) |  | * Cross-Document Contradictions |                   |
|  +---------------------------------+  +---------------------------------+                   |
|                                                                                             |
|  +---------------------------------+  +---------------------------------+                   |
|  |   BOUNDED AGENT (LANGGRAPH)     |  |   RESPONSIBLE AI & CITATION     |                   |
|  | * Deterministic State Machine   |  | * Claim-to-Quote Citation Engine|                   |
|  | * Max 5 Iterations / 30s Timeout|  | * Acute Red-Flag Emergency Guard|                   |
|  | * Human-in-the-Loop Review Gate |  | * Prompt Injection Shield       |                   |
|  +---------------------------------+  +---------------------------------+                   |
+=============================================================================================+
                                              |
                         +--------------------+--------------------+
                         v                                         v
+================================================+ +==========================================+
|         5. DATA PERSISTENCE TIER               | |    6. FOUNDATION MODEL GATEWAY           |
|  * PostgreSQL 16 / Google Cloud SQL:           | |  * Hosted Google Gemini API:             |
|    Patients, Documents, Events, Audit Trails   | |    gemini-flash-latest, flash-lite       |
|  * Qdrant Vector Engine (Cloud or Embedded):   | |  * Local Offline Ollama Engine:          |
|    384-d Vectors, Payload Isolation, HNSW      | |    qwen3:4b (100% offline development)   |
|  * Document Storage: Google Cloud Storage / S3 | |  * Mock Provider (Testing / Zero Cost)   |
+================================================+ +==========================================+
```

---

## 3. System Requirements Specification

### 3.1 Functional Requirements (FR)

| Requirement ID | Domain | Specification |
| :--- | :--- | :--- |
| **FR-AUTH-01** | Authentication | The system shall authenticate users via signed JWT tokens (HS256) with Argon2 password hashing. |
| **FR-AUTH-02** | RBAC | The system shall enforce 4 distinct roles: `admin`, `reviewer`, `researcher`, and `auditor`. |
| **FR-AUTH-03** | Tenant Isolation | The system shall enforce patient-level authorization at database and vector layers. |
| **FR-DOC-01** | Ingestion | The system shall accept PDF uploads up to 25 MB and validate magic bytes (`%PDF-`). |
| **FR-DOC-02** | Deduplication | The system shall compute SHA-256 hashes to prevent duplicate file ingestion. |
| **FR-DOC-03** | Page Provenance | The system shall extract text using PyMuPDF while preserving physical page numbers and coordinates. |
| **FR-DOC-04** | Normalization | The system shall normalize clinical text without altering units (`mg/dL`, `mmHg`) or decimals. |
| **FR-DOC-05** | Chunking | The system shall split text into 512-token semantic chunks with 64-token overlap and document headers. |
| **FR-RET-01** | Embeddings | The system shall generate 384-dimensional dense vectors using FastEmbed (`bge-small-en-v1.5`) on CPU. |
| **FR-RET-02** | Vector Index | The system shall index vectors in Qdrant with payload filters (`patient_id`, `doc_type`, `doc_date`). |
| **FR-RET-03** | Sparse Search | The system shall maintain in-memory Okapi BM25 indices preserving clinical acronyms (`NT-proBNP`, `eGFR`). |
| **FR-RET-04** | Rank Fusion | The system shall merge dense and sparse results using Reciprocal Rank Fusion ($k=60$). |
| **FR-RAG-01** | Context Assembly| The system shall assemble retrieval context under a 2,000 token budget inside untrusted delimiter boundaries. |
| **FR-RAG-02** | Citation Engine | The system shall verify citations post-generation using claim-to-quote matching against source passages. |
| **FR-RAG-03** | Abstention | The system shall abstain deterministically ("Insufficient evidence documented in available records") on ungrounded queries. |
| **FR-TIME-01**| Timeline Events | The system shall extract dated events categorized as Diagnoses, Medications, Procedures, Labs, Encounters, Allergies. |
| **FR-TIME-02**| Temporal Dates | The system shall record `event_date` independently from `document_date` with precision tags. |
| **FR-TIME-03**| Contradictions | The system shall detect cross-document contradictions (e.g. NKDA vs active allergy, quantitative EF decline). |
| **FR-RES-01** | Research Mining | The system shall extract structured PICOS parameters (Population, Intervention, Comparator, Outcomes) from trials. |
| **FR-RES-02** | Evidence Matrix | The system shall construct side-by-side comparative matrices contrasting endpoints across publications. |
| **FR-AGT-01** | Agent Workflow | The system shall execute multi-step research investigations via a deterministic LangGraph state machine. |
| **FR-AGT-02** | Agent Guardrails| The system shall enforce execution bounds: maximum 5 loop iterations, 30-second timeout, read-only tools. |
| **FR-AGT-03** | Review Gate | The system shall require explicit human clinician approval before finalizing generated reports. |
| **FR-SEC-01** | Audit Logging | The system shall record append-only audit events with sensitive credential masking. |
| **FR-SEC-02** | Red-Flag Warning| The system shall scan queries for acute emergency symptoms (cardiac arrest, anaphylaxis, stroke) and display warnings. |
| **FR-SEC-03** | Right to Erasure| The system shall support cascading deletion (`DELETE /api/v1/patients/{id}`) purging records, vectors, and events. |

### 3.2 Non-Functional Requirements (NFR)

* **NFR-PERF-01 (Retrieval Latency):** Hybrid retrieval latency (dense + BM25 + RRF) shall be $\le 1.5\text{s}$ at P95 for dossiers up to 100 documents.
* **NFR-PERF-02 (End-to-End QA):** End-to-end question answering shall complete in $\le 4.0\text{s}$ at P95 using hosted Gemini models.
* **NFR-PERF-03 (Ingestion Throughput):** Document parsing via PyMuPDF shall process at $\ge 15\text{ pages/second}$ on CPU hardware.
* **NFR-RES-01 (Hardware Footprint):** The local stack shall run completely on a 16 GB RAM CPU machine without requiring a dedicated GPU.
* **NFR-RES-02 (Container Budgets):** Containers shall run stably with memory allocations: Backend 1 GB, Frontend 512 MB, PostgreSQL 512 MB, Qdrant 512 MB.
* **NFR-SEC-01 (Tenant Isolation):** Zero cross-patient leakage enforced at SQL query and vector payload filter levels.
* **NFR-SEC-02 (Prompt Injection Defense):** Neutralizes jailbreaks and system override prompts via strict delimiter parsing.
* **NFR-REL-01 (Strict Type Safety):** 100% type annotations across backend Python (Mypy strict) and frontend TypeScript.
* **NFR-REL-02 (Test Verification):** Maintain 100% passing automated test suite with offline mock provider execution.

---

## 4. Data Model and Storage Specifications

Patient360 utilizes a dual persistence architecture:
1. **Relational Database (PostgreSQL 16 / Cloud SQL):** Stores structured medical entities, user accounts, role permissions, clinical timelines, and immutable audit logs.
2. **Vector Database (Qdrant):** Stores dense 384-dimensional vector embeddings with payload metadata filters.

### 4.1 Relational Schema Definitions

```sql
-- Users and Role-Based Access Control
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'reviewer', 'researcher', 'auditor')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Patient Demographic Dossiers
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mrn_synthetic VARCHAR(64) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20) NOT NULL,
    primary_condition VARCHAR(255),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Patient-User Access Permissions (Row-Level Security)
CREATE TABLE user_patient_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL CHECK (permission_level IN ('read', 'write', 'admin')),
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, patient_id)
);

-- Ingested Clinical and Research Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_hash_sha256 VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL DEFAULT 'application/pdf',
    doc_type VARCHAR(50) NOT NULL CHECK (doc_type IN ('patient_record', 'lab_report', 'discharge_summary', 'research_paper', 'clinical_guideline')),
    doc_date DATE,
    ingestion_status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (ingestion_status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    version INT NOT NULL DEFAULT 1,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Semantic Document Chunks with Physical Page Provenance
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    page_number INT NOT NULL,
    content TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    token_count INT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

-- Longitudinal Clinical Events and Contradiction Tracking
CREATE TABLE clinical_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('diagnosis', 'medication', 'procedure', 'encounter', 'lab_result', 'allergy')),
    event_date DATE NOT NULL,
    event_date_precision VARCHAR(20) NOT NULL DEFAULT 'day' CHECK (event_date_precision IN ('day', 'month', 'year', 'approximate')),
    document_date DATE,
    description TEXT NOT NULL,
    value_or_dosage VARCHAR(255),
    clinical_status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (clinical_status IN ('active', 'historical', 'resolved', 'disputed')),
    confidence_score FLOAT NOT NULL DEFAULT 1.0,
    contradiction_flag BOOLEAN NOT NULL DEFAULT FALSE,
    contradiction_details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Extracted Biomedical Research Trials (PICOS Parameters)
CREATE TABLE research_studies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID UNIQUE NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    pmid VARCHAR(32),
    doi VARCHAR(128),
    title TEXT NOT NULL,
    authors TEXT,
    publication_date DATE,
    study_design VARCHAR(100),
    population_description TEXT,
    sample_size INT,
    intervention TEXT,
    primary_outcome TEXT,
    limitations TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Append-Only Audit Trail
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    details_json JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.2 Qdrant Vector Payload Schema
* Collection Name: `patient360_chunks`
* Vector Dimensionality: 384 dimensions (Cosine similarity metric)
* HNSW Parameters: `m = 16`, `ef_construct = 100`
* Indexed Payload Attributes: `patient_id` (Keyword), `document_id` (Keyword), `doc_type` (Keyword), `page_number` (Integer), `chunk_index` (Integer).

---

## 5. API Reference

All endpoints are hosted under base path `/api/v1`. Authentication requires header `Authorization: Bearer <jwt_token>`.

| Domain | Method | Endpoint Path | Role Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/login` | Public | Authenticates credentials and returns JWT access/refresh tokens. |
| **Auth** | `POST` | `/api/v1/auth/refresh` | Public | Exchanges valid refresh token for a new access token. |
| **Auth** | `GET` | `/api/v1/auth/me` | Authenticated | Retrieves profile and role permissions of current user. |
| **Patients** | `GET` | `/api/v1/patients` | Authenticated | Lists all patients assigned to the user's clinical panel. |
| **Patients** | `POST` | `/api/v1/patients` | `admin`, `reviewer` | Creates a new patient demographic record. |
| **Patients** | `GET` | `/api/v1/patients/{id}` | Patient Access | Retrieves demographic dossier for a single patient. |
| **Patients** | `DELETE`| `/api/v1/patients/{id}` | `admin` | Cascades deletion across patient records, documents, vectors, events. |
| **Documents**| `GET` | `/api/v1/documents` | Authenticated | Lists uploaded documents with optional `patient_id` filter. |
| **Documents**| `POST` | `/api/v1/documents` | Patient Access | Uploads multi-page clinical PDF (multipart/form-data). |
| **Documents**| `GET` | `/api/v1/documents/{id}/chunks` | Patient Access | Inspects extracted chunks, page numbers, and token counts. |
| **Documents**| `GET` | `/api/v1/documents/{id}/download` | Patient Access | Downloads binary PDF stream for in-viewer inspection. |
| **Ingestion**| `POST` | `/api/v1/documents/{id}/ingest` | Patient Access | Triggers document text extraction, chunking, and vector indexing. |
| **Search** | `POST` | `/api/v1/vector/search` | Patient Access | Dense vector semantic search with patient isolation filters. |
| **Search** | `POST` | `/api/v1/vector/hybrid-search` | Patient Access | Hybrid search merging BM25 and FastEmbed via RRF ($k=60$). |
| **RAG** | `POST` | `/api/v1/rag/query` | Patient Access | Executes grounded clinical QA with claim-to-quote verification. |
| **RAG** | `POST` | `/api/v1/rag/feedback` | Patient Access | Submits clinician rating and feedback on generated responses. |
| **Timeline** | `GET` | `/api/v1/timeline/patients/{id}` | Patient Access | Retrieves chronological clinical timeline with contradiction flags. |
| **Timeline** | `POST` | `/api/v1/timeline/patients/{id}/extract` | Patient Access | Triggers automated clinical event and contradiction extraction. |
| **Agents** | `POST` | `/api/v1/agents/runs` | Patient Access | Launches multi-step clinical investigation workflow in LangGraph. |
| **Agents** | `GET` | `/api/v1/agents/runs/{run_id}` | Patient Access | Retrieves execution status, steps, and pending human review gates. |
| **Agents** | `POST` | `/api/v1/agents/runs/{run_id}/review` | Patient Access | Clinician approves or rejects synthesized investigation report. |
| **Research** | `GET` | `/api/v1/research/studies` | Authenticated | Lists extracted biomedical publications and clinical trials. |
| **Research** | `POST` | `/api/v1/research/compare` | Authenticated | Generates comparative PICOS matrix across selected studies. |
| **Research** | `POST` | `/api/v1/research/export` | Authenticated | Exports synthesized biomedical evidence dossier in Markdown. |
| **Evaluation**| `GET` | `/api/v1/evaluation/runs` | `admin`, `reviewer` | Lists historical benchmark evaluation test executions. |
| **Evaluation**| `POST` | `/api/v1/evaluation/runs` | `admin`, `reviewer` | Executes 50-item synthetic clinical QA benchmark suite. |
| **Health** | `GET` | `/api/v1/health` | Public | Returns system health, component latencies, and provider status. |
| **Metrics** | `GET` | `/metrics` | Public | Exposes Prometheus telemetry metrics for operational scraping. |

---

## 6. Benchmark Evaluation Results

Evaluated against the version-controlled 50-item synthetic clinical benchmark dataset:

| Benchmark Metric | Dense Retrieval | Hybrid RRF (BM25 + Dense) | Measurement Description |
| :--- | :---: | :---: | :--- |
| **Recall@5** | 84.0% | 96.0% | Top-5 relevant chunk recall across clinical queries |
| **Mean Reciprocal Rank (MRR)** | 0.72 | 0.89 | Reciprocal rank of first ground-truth citation passage |
| **Faithfulness Score** | 88.5% | 96.2% | Proportion of generated claims grounded in source text |
| **Answer Relevance** | 89.1% | 94.8% | Semantic alignment to clinical inquiry |
| **Citation Precision** | 81.3% | 92.4% | Exact page-level passage attribution accuracy |
| **Hallucination Rate** | 6.2% | 1.8% | Unsupported assertions detected in answers |
| **Median Latency (CPU)** | 620 ms | 420 ms | End-to-end query processing time |

---

## 7. Google Cloud Platform (GCP) Deployment Guide

Patient360 is engineered for serverless, autoscaling deployment on Google Cloud Platform:

```
+=============================================================================================+
|                               GOOGLE CLOUD RUN ARCHITECTURE                                 |
|                                                                                             |
|  [Clinician Browser] ---> [Cloud Run: Frontend] ---> [Cloud Run: Backend]                   |
|                                                            |                                |
|                        +-----------------------------------+--------------------+           |
|                        |                                   |                    |           |
|                        v                                   v                    v           |
|                 [Cloud SQL: Postgres]             [Secret Manager]      [Gemini API]        |
|                                                                                             |
+=============================================================================================+
```

### 7.1 Prerequisites
* Google Cloud SDK (`gcloud` CLI installed and authenticated).
* A Google Cloud Project with billing enabled.

### 7.2 Automated One-Command Deployment

Run the included automated deployment script:

* **Linux / macOS:**
```bash
chmod +x deployment/gcp/deploy.sh
./deployment/gcp/deploy.sh
```

* **Windows (PowerShell):**
```powershell
.\deployment\gcp\deploy.ps1
```

### 7.3 Manual Step-by-Step Google Cloud Deployment

#### 1. Configure Project and Enable Services
```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

gcloud config set project $PROJECT_ID

gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    sqladmin.googleapis.com
```

#### 2. Create Artifact Registry Repository
```bash
gcloud artifacts repositories create patient360 \
    --repository-format=docker \
    --location=$REGION \
    --description="Patient360 Docker Container Repository"
```

#### 3. Build and Deploy Backend to Cloud Run
```bash
# Build container image via Cloud Build
gcloud builds submit \
    --tag "${REGION}-docker.pkg.dev/${PROJECT_ID}/patient360/backend:latest" \
    -f deployment/docker/backend.Dockerfile .

# Deploy container to Cloud Run
gcloud run deploy patient360-backend \
    --image "${REGION}-docker.pkg.dev/${PROJECT_ID}/patient360/backend:latest" \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 60s \
    --concurrency 80 \
    --set-env-vars ENVIRONMENT=production,DEBUG=false,LLM_PROVIDER=gemini,GEMINI_MODEL=gemini-flash-latest,GEMINI_API_KEY="your-api-key"
```

#### 4. Build and Deploy Frontend to Cloud Run
```bash
# Build frontend container image
gcloud builds submit \
    --tag "${REGION}-docker.pkg.dev/${PROJECT_ID}/patient360/frontend:latest" \
    -f deployment/docker/frontend.Dockerfile .

# Deploy frontend to Cloud Run
gcloud run deploy patient360-frontend \
    --image "${REGION}-docker.pkg.dev/${PROJECT_ID}/patient360/frontend:latest" \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1
```

---

## 8. Localhost Development Quickstart

### 8.1 Prerequisites
* Python 3.11+
* Node.js 18+ or 20+
* Git

### 8.2 Setup Commands

1. Clone repository and initialize Python virtual environment:
```bash
git clone https://github.com/Yanshuptl18/Patient360.git
cd Patient360

python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

2. Seed database with synthetic demonstration cohorts:
```bash
python scripts/seed_demo_data.py
```
*Note: If external PostgreSQL or Qdrant services are not running, the seeder automatically falls back to local SQLite (`./patient360_dev.db`) and embedded vector memory.*

3. Start servers:
```bash
# Terminal 1: Backend API (runs on http://127.0.0.1:8000)
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend Workspace (runs on http://127.0.0.1:5173)
cd frontend
npm install
npm run dev
```

---

## 9. Production Multi-Container Docker Deployment

Launch the hardened container stack locally or on a VPS:

```bash
docker-compose -f deployment/docker-compose.prod.yml up -d
```

### Services Deployed
* `nginx` (Port 80): Reverse proxy with security headers, Gzip compression, and asset caching.
* `backend` (Port 8000): Multi-stage Python 3.11 container running under unprivileged user `appuser` (UID 10001).
* `frontend` (Port 80 internal): Multi-stage container serving the optimized React single-page application.
* `postgres` (Port 5432): Relational database with health checking and persistent volume storage.
* `qdrant` (Port 6333): High-performance vector database on an isolated bridge network.

---

## 10. Quality Assurance and Testing

Patient360 maintains continuous verification with 100% offline-executable tests:

```bash
# Run automated test suite (151 tests)
pytest -v

# Python code formatting and linting
ruff check .

# Strict static type verification
mypy backend

# Frontend TypeScript validation and production build
cd frontend && npm run build
```

---

## 11. Architectural Decisions (ADR Summary)

| ADR ID | Decision Title | Selected Option | Rationale |
| :--- | :--- | :--- | :--- |
| **ADR-001** | Vector Store Selection | Qdrant | Fast CPU performance, native payload filtering, embedded fallback mode. |
| **ADR-002** | Embedding Model | BAAI/bge-small-en-v1.5 | 384 dimensions, strong MTEB clinical retrieval score, fast CPU execution via FastEmbed. |
| **ADR-003** | PDF Parsing Engine | PyMuPDF (fitz) | Page-aware coordinate extraction, zero heavy Java/OCR runtime dependencies. |
| **ADR-004** | Hybrid Retrieval Algorithm | Reciprocal Rank Fusion ($k=60$) | Robust merger of sparse BM25 and dense FastEmbed without parameter tuning. |
| **ADR-005** | Agent Framework | LangGraph | Deterministic state machine, loop cycle bounding (max 5), human-in-the-loop review. |
| **ADR-006** | Database Abstraction | SQLAlchemy 2.0 Core/ORM | Clean declarative models, connection pooling, and automatic SQLite fallback. |
| **ADR-007** | LLM Gateway Architecture | Native HTTPX Provider Gateway | Provider-agnostic support for Gemini, Ollama, and Mock without heavy vendor SDK locks. |
| **ADR-008** | Client Architecture | React 18 + TypeScript + Vite | Clean component architecture, strict type safety, fast Vite build bundle. |

---

## 12. License and Acknowledgements

* **License:** MIT License. See [LICENSE](LICENSE) for details.
* **Clinical Knowledge Sources:** Synthetic patient dossiers modeled on standard clinical case reporting guidelines. Landmark clinical trials cited from the *New England Journal of Medicine* (NEJM).
* **Open Source Ecosystem:** Powered by FastAPI, React, Qdrant, FastEmbed, PyMuPDF, SQLAlchemy, and Prometheus.
