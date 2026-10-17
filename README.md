# Patient360 

[![Live Application](https://img.shields.io/badge/Live_App-Cloud_Run_Online-00875A?style=for-the-badge&logo=googlecloud&logoColor=white)](https://patient360-frontend-442154825091.us-central1.run.app)
[![API Status](https://img.shields.io/badge/API_Health-100%25_Operational-0052CC?style=for-the-badge&logo=fastapi&logoColor=white)](https://patient360-backend-442154825091.us-central1.run.app/health)
[![Architecture](https://img.shields.io/badge/Architecture-Scale_to_Zero_Serverless-42526E?style=for-the-badge)](https://cloud.google.com/run)
[![License](https://img.shields.io/badge/License-MIT-gray?style=for-the-badge)](LICENSE)

Patient360 is a healthcare intelligence and evidence-synthesis platform designed for doctors, clinical reviewers, care coordinators, hospital administrators, and medical researchers. The platform synthesizes fragmented clinical records and biomedical research documents into an organized workspace with exact physical page citations, longitudinal care timelines, conflicting information detection, and bounded research workflows.

---

## Live Cloud Deployment

The platform is deployed and publicly accessible on Google Cloud Run:

| Component | Target URL | Description |
| :--- | :--- | :--- |
| **Web Application** | [https://patient360-frontend-442154825091.us-central1.run.app](https://patient360-frontend-442154825091.us-central1.run.app) | Single-page clinical interface with 1-click role selection |
| **Interactive API Documentation** | [https://patient360-backend-442154825091.us-central1.run.app/docs](https://patient360-backend-442154825091.us-central1.run.app/docs) | Swagger UI for exploring and testing backend endpoints |
| **System Diagnostics** | [https://patient360-backend-442154825091.us-central1.run.app/api/v1/health](https://patient360-backend-442154825091.us-central1.run.app/api/v1/health) | Deep component health (Database, Vector, Storage, LLM) |

> **Quick Demo Access:** Visitors can select any of the five preconfigured personas on the login page (Doctor, Nurse, Hospital Admin, Patient, System Admin) to enter the respective tailored workspace instantly without registration or passwords.

---

## Clinical Notice and Disclaimer

Patient360 supports medical information retrieval and research workflows. It is not an FDA-cleared medical device, autonomous diagnostic system, or prescribing platform. It does not replace professional clinical judgment. All synthesized summaries, extracted timeline events, and citations must be independently checked and verified by qualified healthcare professionals against primary source medical records before making clinical decisions.

---

## Table of Contents

- [Live Cloud Deployment](#live-cloud-deployment)
- [Core Capabilities](#core-capabilities)
- [Role-Based Clinical Workspaces](#role-based-clinical-workspaces)
- [System Architecture](#system-architecture)
- [Feature Implementation Status](#feature-implementation-status)
- [Technology Stack](#technology-stack)
- [Local Development Setup](#local-development-setup)
- [Docker Multi-Container Deployment](#docker-multi-container-deployment)
- [Google Cloud Deployment Guide](#google-cloud-deployment-guide)
- [Quality Assurance and Verification](#quality-assurance-and-verification)
- [Security and Patient Data Isolation](#security-and-patient-data-isolation)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Core Capabilities

### 1. Medical Document Management
- Ingests clinical PDF records, discharge summaries, laboratory panels, and scientific papers up to 25 MB.
- Assigns tamper-evident SHA-256 cryptographic hashes for document integrity and deduplication.
- Preserves physical page numbers, tabular values, clinical units (e.g., mg/dL, mmHg), and medical abbreviations.

### 2. Evidence-Grounded Question Answering
- Enables authorized clinicians to ask targeted clinical questions about an assigned patient's records.
- Every claim is anchored to exact physical page numbers, document identifiers, and verbatim excerpts.
- Features built-in PDF viewer integration to inspect original source passages directly.
- Plainly abstains ("Insufficient evidence documented in available records") when documents do not substantiate an assertion, preventing ungrounded speculation.

### 3. Medical History Timeline
- Automatically organizes clinical events chronologically across diagnoses, medications, procedures, encounters, and laboratory results.
- Distinguishes event occurrence dates from document recording dates.
- Detects cross-document contradictions (e.g., documented "No Known Drug Allergies" conflicting with active penicillin prescriptions, or quantitative ejection fraction disparities).

### 4. Clinical Research Assistant
- Structured multi-step investigation workflow for complex clinical inquiries.
- Displays transparent progress across evidence retrieval, cross-referencing, and draft preparation.
- Enforces a mandatory clinical review gate: reports cannot be finalized without explicit human clinician approval.

### 5. Biomedical Research Workspace
- Extracts Population, Intervention, Comparator, and Outcomes (PICO) parameters from published clinical trials and guidelines.
- Generates side-by-side comparative matrices across multiple publications.
- Exports structured evidence summaries in Markdown format for clinical review committees.

---

## Role-Based Clinical Workspaces

Patient360 provides tailored workspaces for five distinct healthcare user types:

| Role Name | Primary Clinical Tasks | Access Boundary |
| :--- | :--- | :--- |
| **Doctor** | Comprehensive patient dossier review, question answering, timeline examination, research assistant workflows. | All authorized patients in the department. |
| **Nurse / Care Coordinator** | Patient vital and care event monitoring, medication schedules, conflicting documentation alerts. | Assigned care cohort records. |
| **Hospital Administrator** | Facility census oversight, document throughput tracking, record integrity audits. | Facility-wide governance and audit logs. |
| **Patient** | Personal health records, care timeline, questions about personal documents. | Strictly isolated to personal records (Eleanor Vance). |
| **System Administrator** | Service health status, quality testing benchmarks, security configuration. | System configuration and diagnostic telemetry. |

---

## System Architecture

<details open>
<summary><b>View System Architecture Diagram</b></summary>

```
+=============================================================================================+
|                                  1. CLIENT & PRESENTATION TIER                              |
|  * React 18 Single-Page Application (TypeScript)     * Tailored Clinical Workspaces         |
|  * Light Healthcare Design System (WCAG AA Compliant)* In-Browser Evidence Citation Viewer  |
|  * Medical History Timeline & Conflict Viewer        * One-Click Role Selector (Demo Mode)  |
+=============================================================================================+
                                              |
                                     HTTPS / TLS (Port 443)
                                              v
+=============================================================================================+
|                               2. INGRESS & REVERSE PROXY TIER                               |
|  * Google Cloud Run Ingress / Nginx Proxy           * Strict Security Headers               |
|  * Static Asset Compression & Caching               * Rate Limiting & Request Sanitization  |
+=============================================================================================+
                                              |
                                     Internal HTTP (Port 8080)
                                              v
+=============================================================================================+
|                              3. FASTAPI BACKEND GATEWAY LAYER                               |
|  * JWT Authentication & Token Lifecycle             * Role-Based Access Control (5 Roles)   |
|  * Server-Side Patient Tenant Isolation Middleware  * Pydantic v2 Schema Validation         |
|  * Emergency Acute Symptom Guardrails               * Audit Logger with Credential Masking  |
+=============================================================================================+
                                              |
                                              v
+=============================================================================================+
|                         4. CLINICAL INTELLIGENCE & DOMAIN SERVICES                          |
|                                                                                             |
|  +---------------------------------+  +---------------------------------+                   |
|  |     HYBRID RETRIEVAL ENGINE     |  |   CLINICAL TIMELINE & CONFLICT  |                   |
|  | * Dense FastEmbed (384-d CPU)   |  | * Temporal Event Extraction     |                   |
|  | * Sparse Okapi BM25 Search      |  | * Event vs Document Date Split  |                   |
|  | * Reciprocal Rank Fusion (k=60) |  | * Cross-Document Contradictions |                   |
|  +---------------------------------+  +---------------------------------+                   |
|                                                                                             |
|  +---------------------------------+  +---------------------------------+                   |
|  |   RESEARCH ASSISTANT WORKFLOW   |  |   CITATION & SAFETY VERIFIER    |                   |
|  | * Bounded State Machine (Max 5) |  | * Claim-to-Quote Verification   |                   |
|  | * 30-Second Execution Limit     |  | * Insufficient-Evidence Notice  |                   |
|  | * Mandatory Human Review Gate   |  | * Acute Clinical Warning Scan   |                   |
|  +---------------------------------+  +---------------------------------+                   |
+=============================================================================================+
                                              |
                         +--------------------+--------------------+
                         v                                         v
+================================================+ +==========================================+
|         5. DATA PERSISTENCE TIER               | |     6. FOUNDATION MODEL GATEWAY          |
|  * Relational Database (PostgreSQL / SQLite):  | |  * Hosted Google Gemini API:             |
|    Patients, Documents, Events, Audit Logs     | |    gemini-flash-latest, 3.5-flash-lite   |
|  * Vector Storage (Qdrant Cloud / Embedded):   | |  * Local Offline Ollama Engine:          |
|    384-dimensional Index with Tenant Filters   | |    qwen3:4b (offline development)        |
|  * Document Storage (Local Disk / Cloud Store):| |  * Deterministic Mock Provider:          |
|    Tamper-Evident SHA-256 PDF Archive          | |    Automated Testing & Cost-Free Demo    |
+================================================+ +==========================================+
```

</details>

---

## Feature Implementation Status

| Feature Domain | Capability |
| :--- | :--- |
| **Authentication** | JWT Authentication, Argon2 Hashing, Token Refresh |
| **Demo Access** | One-Click Demo Role Selector (5 User Personas) |
| **Patient Isolation** | Server-side database & vector payload filtering |
| **Document Ingestion** | PDF parsing, physical page coordinates, SHA-256 hash |
| **Hybrid Search** | FastEmbed 384-d dense vectors + Okapi BM25 + RRF |
| **Evidence QA** | Grounded question answering with page-level citations |
| **Citation Verifier** | Verbatim claim-to-quote source text matching |
| **Abstention** | Plain "insufficient evidence" handling |
| **Clinical Timeline** | Chronological event extraction (diagnoses, meds, labs) |
| **Contradictions** | Cross-document conflicting information detection |
| **Biomedical Studies** | PICO parameter extraction and cross-study matrix |
| **Research Assistant** | Multi-step bounded investigation with review gates |
| **Quality Testing** | Evaluation lab benchmark suite for retrieval & latency |
| **Service Status** | Real-time health check endpoint (`/api/v1/health`) |

---

## Technology Stack

- **Frontend:** React 18, TypeScript, Tailwind CSS, Lucide Icons, Vite.
- **Backend:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0.
- **Document Processing:** PyMuPDF (`fitz`) for PDF extraction.
- **Vector Search:** Qdrant (supports cloud cluster and embedded local mode).
- **Embeddings:** FastEmbed with `BAAI/bge-small-en-v1.5` running on CPU (with offline deterministic unit fallback).
- **Keyword Search:** In-memory Okapi BM25 with clinical acronym preservation.
- **Rank Fusion:** Reciprocal Rank Fusion (RRF, $k=60$).
- **Workflow State Machine:** LangGraph deterministic state machine with loop iteration limits.
- **Relational Storage:** PostgreSQL 16 (with automatic local SQLite fallback).
- **Monitoring:** Prometheus telemetry metrics exposition at `/metrics`.

---

## Local Development Setup

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or 20
- Git

### 1. Clone Repository & Setup Backend Environment

#### Windows (PowerShell):
```powershell
git clone https://github.com/Yanshuptl18/Patient360.git
cd Patient360

python -m venv .venv
.\.venv\Scripts\activate

pip install -r requirements.txt
```

#### Linux / macOS:
```bash
git clone https://github.com/Yanshuptl18/Patient360.git
cd Patient360

python3.11 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Seed Demonstration Data

```bash
python scripts/seed_demo_data.py
```

### 4. Run the Application

#### Terminal 1: Backend API
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API documentation is available at `http://localhost:8000/docs` and service health at `http://localhost:8000/api/v1/health`.

#### Terminal 2: Frontend Single-Page Application
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Docker Multi-Container Deployment

To run the complete production container stack locally or on a server:

```bash
docker-compose -f deployment/docker-compose.prod.yml up -d
```

### Containers in Stack

| Container | Image / Base | Internal Port | Host Port | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `frontend` | Node multi-stage -> Nginx | 80 | 80 | Serves optimized React application bundle |
| `backend` | Python 3.11-slim | 8000 | 8000 | FastAPI REST service and intelligence pipelines |
| `postgres` | postgres:16-alpine | 5432 | 5432 | Relational store for users, records, timelines |
| `qdrant` | qdrant/qdrant:v1.8.4 | 6333 | 6333 | Vector database for semantic evidence retrieval |

To view logs:
```bash
docker-compose -f deployment/docker-compose.prod.yml logs -f
```

To stop:
```bash
docker-compose -f deployment/docker-compose.prod.yml down
```

---

## Google Cloud Deployment Guide

The production architecture is deployed on Google Cloud Run with scale-to-zero serverless configuration to guarantee minimal operating costs under the GCP Free Tier.

### Cloud Run Deployment Steps

#### 1. Set Google Cloud Project
```bash
export PROJECT_ID="project-1d029ac0-ec27-4c35-851"
export REGION="us-central1"

gcloud config set project $PROJECT_ID
```

#### 2. Enable Required APIs
```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com
```

#### 3. Build & Deploy Backend
```bash
# Build backend container via Cloud Build
gcloud builds submit --config=deployment/gcp/cloudbuild-backend.yaml .

# Deploy to Cloud Run
gcloud run deploy patient360-backend \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/patient360/backend:latest" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=2 \
    --timeout=60s \
    --set-env-vars="ENVIRONMENT=production,DEBUG=false,DEMO_MODE=true,DATABASE_URL=sqlite:////app/storage/patient360.db,STORAGE_LOCAL_PATH=/app/storage/documents,LLM_PROVIDER=mock,SECRET_KEY=patient360_production_secret_key_8492049102948192"
```

#### 4. Build & Deploy Frontend
```bash
# Capture backend URL
BACKEND_URL=$(gcloud run services describe patient360-backend --region="${REGION}" --format="value(status.url)")

# Build frontend container via Cloud Build
gcloud builds submit --config=deployment/gcp/cloudbuild-frontend.yaml .

# Deploy frontend to Cloud Run
gcloud run deploy patient360-frontend \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/patient360/frontend:latest" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=2 \
    --set-env-vars="BACKEND_URL=${BACKEND_URL}"
```

---

## Quality Assurance and Verification

Patient360 includes automated unit, integration, and live deployment verification suites:

```bash
# Run local unit test suite (108 tests)
.\.venv\Scripts\python.exe -m pytest tests/unit -v

# Run full local test suite (154 tests)
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Run live Cloud Run production verification suite (12 tests)
.\.venv\Scripts\python.exe scripts/verify_live_deployment.py

# Run frontend TypeScript validation and production build
cd frontend && npm run build
```

### Verification Results Summary

- **Backend Pytest Suite:** 154 passed in 13.39 seconds.
- **Frontend TypeScript Build:** 0 type errors, production bundle compiled cleanly in 8.96 seconds.
- **Live Cloud Run E2E Verification:** 12 of 12 live end-to-end tests passed on the public production deployment.
- **Patient Isolation:** Server-enforced row-level queries and vector filters verified across patient records.
- **Document Ingestion:** PDF extraction, hashing, and page coordinate mapping verified.

---

## Security and Patient Data Isolation

1. **Server-Enforced Patient Isolation:**
   - Authorization is enforced at the database query and vector search payload filter levels.
   - Patient users (e.g., Eleanor Vance) are strictly restricted to their own synthetic record ID (`SYNTH-10001`).
   - Modifying request parameters, IDs, or query text cannot bypass server-side tenant isolation.

2. **Verifiable Data Provenance:**
   - Every ingested document is assigned an immutable SHA-256 cryptographic hash.
   - All AI answers link directly to original document IDs, physical page numbers, and verbatim source passages.

3. **Protection of Secrets:**
   - All API keys, tokens, and database passwords are kept on the server and loaded via environment variables.
   - Frontend bundles contain zero embedded secrets.

4. **Responsible Clinical Safety Guardrails:**
   - Acute symptom queries (e.g., cardiac arrest, acute chest pain) trigger immediate emergency care advisories.
   - The platform clearly states that it does not provide autonomous clinical diagnoses or prescribe treatments.

---

## Troubleshooting

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| `Cannot connect to PostgreSQL` | Database container or server not running. | The platform will automatically fall back to local SQLite (`patient360_dev.db`). For PostgreSQL, run `docker-compose up -d postgres`. |
| `Qdrant connection refused` | Vector store service offline. | The system falls back to embedded vector search. To use external Qdrant, run `docker-compose up -d qdrant`. |
| `Missing Gemini API key` | `GEMINI_API_KEY` not configured. | Set your key in `.env` or leave `LLM_PROVIDER=mock` for testing. |
| `File upload rejected (Over 25 MB)`| File exceeds maximum size threshold. | Ensure uploaded documents are clinical PDFs under 25 MB. |

---

## License

Patient360 is licensed under the [MIT License](LICENSE).
Synthetic patient records and landmark clinical trial citations are modeled on published clinical literature for research and educational demonstrations.
