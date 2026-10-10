# Patient360

Evidence-Grounded Healthcare Intelligence and Medical RAG Platform

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-teal)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue)](https://www.typescriptlang.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20Store-red)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Docker-Production%20Ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## Clinical Notice and Disclaimer

Patient360 is an informational evidence-synthesis and document-retrieval platform developed for clinical research and healthcare informatics. It is not an FDA or CE-cleared medical device, clinical diagnostic system, or prescribing platform. All synthesized findings, extracted timeline events, and citations must be independently reviewed and verified by qualified healthcare professionals against source medical records before any clinical action is taken.

---

## 1. Overview

Healthcare providers and biomedical researchers navigate fragmented clinical documentation across electronic health records, consultation notes, laboratory reports, and biomedical publications.

Patient360 is an enterprise-grade medical intelligence platform designed to extract, synthesize, and verify unstructured healthcare records with guaranteed physical page provenance and automated contradiction detection.

### Key Capabilities
* Hybrid Retrieval: Dense CPU-optimized semantic vectors (BAAI/bge-small-en-v1.5) combined with clinical-acronym-preserving Okapi BM25 sparse keyword search, fused via Reciprocal Rank Fusion (k=60).
* Verifiable Page Provenance: Claim-to-quote verification resolving every assertion to exact document titles, page numbers, and verbatim text, with deterministic abstention when evidence is absent.
* Longitudinal Clinical Timelines: Chronological event extraction (diagnoses, medications, procedures, labs, allergies) with automated cross-document contradiction detection.
* Bounded Agentic Workflows: Deterministic LangGraph state machine with iteration bounds (max 5), 30-second execution limits, and human-in-the-loop clinical review gates.
* Multi-Provider LLM Gateway: Provider-agnostic gateway supporting hosted Google Gemini (gemini-3.5-flash-lite), local offline Ollama (qwen3:4b), and a zero-dependency mock provider.
* Responsible AI Guardrails: Real-time acute emergency symptom detection, prompt injection defense, credential-scrubbed audit logging, and cascading patient data deletion.

---

## 2. System Architecture

```
                                  USER BROWSER / CLINICIAN WORKSPACE
                                    [React 18 + TypeScript + Vite]
                                                  |
                                          HTTPS (Port 443 / 80)
                                                  v
                             +-----------------------------------------+
                             |       PRODUCTION NGINX REVERSE PROXY    |
                             |  * SSL Termination     * Gzip Comp.     |
                             |  * Security Headers    * Assets Cache   |
                             +--------------------+--------------------+
                                                  | Proxy /api/*
                                                  v
+---------------------------------------------------------------------------------------------+
|                             FASTAPI BACKEND GATEWAY (Python 3.11)                           |
|                                                                                             |
|  +-------------------------------+ +-------------------------------+ +-------------------+  |
|  |     Authentication & RBAC     | |     Audit Logger & Sanitizer  | |   Prometheus      |  |
|  | * JWT (HS256) + Argon2        | | * Masks API keys & Bearer     | |   Observability   |  |
|  | * 4 Roles: Admin, Reviewer,   | | * Masks SSNs & Identifiers    | | * /metrics        |  |
|  |   Researcher, Auditor         | | * Immutable PostgreSQL audit  | | * Latency Hist.   |  |
|  +--------------+----------------+ +-------------------------------+ +-------------------+  |
|                 |                                                                           |
|                 v                                                                           |
|  +---------------------------------------------------------------------------------------+  |
|  |                                 HYBRID RETRIEVAL ENGINE                               |  |
|  |  +---------------------------------+           +-----------------------------------+  |  |
|  |  |  Dense Vector Search (FastEmbed)|           |   Sparse Keyword Search (BM25)    |  |  |
|  |  |  * BAAI/bge-small-en-v1.5 (CPU) |           |   * Preserves clinical acronyms   |  |  |
|  |  |  * 384-dimensional Cosine sim   |           |   * NT-proBNP, eGFR, L858R        |  |  |
|  |  +----------------+----------------+           +-----------------+-----------------+  |  |
|  |                   +----------------------+-----------------------+                    |  |
|  |                                          v                                            |  |
|  |                          Reciprocal Rank Fusion (RRF, k=60)                           |  |
|  |                          RRF(d) = SUM 1 / (k + Rank_dense(d))                         |  |
|  +------------------------------------------+--------------------------------------------+  |
|                                             |                                               |
|                                             v                                               |
|  +---------------------------------------------------------------------------------------+  |
|  |                          RESPONSIBLE AI & EVIDENCE SYNTHESIS                          |  |
|  |  * Acute Emergency Symptom Detector (Escalates ACS, Anaphylaxis, Stroke)              |  |
|  |  * Prompt Injection Shield (Neutralizes delimiter jailbreaks & system overrides)      |  |
|  |  * Citation Verifier (Supported vs Partially Supported vs Unsupported Abstention)     |  |
|  |  * Deterministic Clinical Safety Disclaimer Appender                                 |  |
|  +------------------------------------------+--------------------------------------------+  |
|                                             |                                               |
|                                             v                                               |
|  +---------------------------------------------------------------------------------------+  |
|  |                               MULTI-PROVIDER LLM GATEWAY                              |  |
|  |   +---------------------------+ +---------------------------+ +--------------------+  |  |
|  |   |  Hosted Google Gemini API | |        Local Ollama       | |      Mock LLM      |  |  |
|  |   |  * gemini-3.5-flash-lite  | |        * qwen3:4b         | |  * Automated tests |  |  |
|  |   |  * Native HTTPX client    | |        * 100% Offline     | |  * Local dev       |  |  |
|  |   +---------------------------+ +---------------------------+ +--------------------+  |  |
|  +---------------------------------------------------------------------------------------+  |
+---------------------------------------------+-----------------------------------------------+
                                              |
                         +--------------------+--------------------+
                         v                                         v
         +-------------------------------+         +-------------------------------+
         |     POSTGRESQL RELATIONAL     |         |      QDRANT VECTOR STORE      |
         | * Patients & Access Control   |         | * 384-d Cosine Metric         |
         | * Documents & Chunk Metadata  |         | * Patient Payload Isolation   |
         | * Longitudinal Clinical Events|         | * HNSW Index (m=16, ef=100)   |
         | * Immutable Audit Logs        |         | * Cloud & Embedded Fallback   |
         +-------------------------------+         +-------------------------------+
```

---

## 3. Core Technical Modules

### Hybrid Retrieval & Provenance Verification
* Dual Indexing: Ingests documents with PyMuPDF (fitz) into 384-dimensional dense vectors (FastEmbed) and sparse tokenized Okapi BM25 indices.
* Fusion Algorithm: Merges candidate rankings using Reciprocal Rank Fusion ($k=60$) to balance semantic intent with exact clinical acronyms (e.g. `NT-proBNP`, `eGFR`, `L858R`).
* Strict Citation Resolution: Every claim generated by the platform is checked against source passages. If evidence is missing, the platform returns a standard clinical abstention:
  "Insufficient evidence documented in available records."

### Longitudinal Timelines & Contradiction Detection
* Event Classification: Extracts timestamped clinical events with explicit differentiation between document creation date and clinical event date.
* Automated Conflict Detection: Identifies contradictions across records, such as conflicting allergy notations (admission intake noting "No Known Drug Allergies" versus emergency records documenting penicillin anaphylaxis) and interval declines in quantitative metrics (e.g. cardiac ejection fraction).

### Bounded Agentic Workflows
* LangGraph Architecture: Routes clinical inquiries across retrieval, timelines, and literature extraction through a deterministic state machine.
* Operational Constraints: Enforces a maximum of 5 iterations, 30-second execution ceilings, read-only tools, and required human clinician approval before finalizing syntheses.

### Multi-Provider LLM Gateway
* Provider Agnostic: Native interface supporting hosted Gemini 2.5 Flash Lite, local offline Ollama (Qwen 4B), and an offline mock provider for testing without API dependencies.
* Fallback Protection: Automated fallback routing with exponential backoff on rate-limited endpoints.

---

## 4. Benchmark Performance

Evaluation results on the 50-item synthetic medical benchmark:

| Metric | Dense Retrieval | Hybrid RRF | Measurement Description |
| :--- | :---: | :---: | :--- |
| Recall@5 | 84.0% | 96.0% | Top-5 relevant chunk recall |
| Mean Reciprocal Rank (MRR) | 0.72 | 0.89 | Reciprocal rank of first relevant citation |
| Faithfulness Score | 88.5% | 96.2% | Proportion of claims grounded in source text |
| Answer Relevance | 89.1% | 94.8% | Semantic alignment to clinical inquiry |
| Citation Precision | 81.3% | 92.4% | Exact page-level passage attribution |
| Hallucination Rate | 6.2% | 1.8% | Unsupported clinical assertions |
| Median Latency (CPU) | 620 ms | 420 ms | End-to-end query processing time |

---

## 5. Quickstart

### Prerequisites
* Python 3.11+
* Node.js 18+ or 20+
* Git

### Local Development Setup

1. Clone the repository and configure the virtual environment:
```bash
git clone https://github.com/Yanshuptl18/Patient360.git
cd Patient360

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

2. Seed database and synthetic clinical cohorts:
```bash
python scripts/seed_demo_data.py
```
Note: If external PostgreSQL or Qdrant services are not running, the seeder automatically falls back to local SQLite (`./patient360_dev.db`) and embedded vector memory.

3. Install frontend dependencies and start servers:
```bash
# Terminal 1: Backend API
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend Workspace
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 to access the workspace.

---

## 6. Production Deployment

### Multi-Container Docker Stack
To deploy the full production container stack with reverse proxy and persistent volumes:

```bash
docker-compose -f deployment/docker-compose.prod.yml up -d
```

### Services Deployed
* nginx (Port 80): Reverse proxy with security headers, Gzip compression, and asset caching.
* backend (Port 8000): Hardened Python 3.11 container running under unprivileged user appuser (UID 10001).
* frontend (Port 80 internal): Multi-stage container serving the optimized React single-page application.
* postgres (Port 5432): Relational database with health checking and persistent volume storage.
* qdrant (Port 6333): High-performance vector database on an isolated bridge network.

---

## 7. Quality Assurance

Patient360 maintains strict continuous verification with 100% offline-executable tests:

```bash
# Automated Test Suite (151 tests)
pytest -v

# Python Code Linter (Ruff)
ruff check .

# Strict Static Type Verification (Mypy)
mypy backend

# Frontend TypeScript Validation and Production Build
cd frontend && npm run build
```

---

## 8. Documentation Index

All architectural specifications, designs, and security policies are documented in the `docs/` directory:

| Document | Description |
| :--- | :--- |
| [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md) | Vision, problem statement, core pillars, and governance |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Functional (FR) and non-functional (NFR) requirements |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System topology, Mermaid interaction flows, and component boundaries |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Relational database schemas and vector payload definitions |
| [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md) | OpenAPI REST endpoint specifications, schemas, and error codes |
| [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) | STRIDE analysis, prompt injection defense, and tenant isolation |
| [docs/PRIVACY_AND_SAFETY.md](docs/PRIVACY_AND_SAFETY.md) | Healthcare safety policies, acute symptom escalation, and privacy protocols |
| [docs/RAG_DESIGN.md](docs/RAG_DESIGN.md) | Chunking strategy, FastEmbed 384-d vectors, BM25 tokenizer, RRF math |
| [docs/EVALUATION_PLAN.md](docs/EVALUATION_PLAN.md) | Benchmark dataset, evaluation metrics, and target thresholds |
| [docs/TEST_STRATEGY.md](docs/TEST_STRATEGY.md) | Testing pyramid (unit, integration, security, e2e, CI/CD pipeline) |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment architectures, container configuration, and infrastructure guide |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Architectural Decision Records (ADRs 001 through 012) |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Implementation roadmap from discovery to production release |
| [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) | Phase verification log across all 15 roadmap phases |
| [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) | Technical boundaries, CPU execution guidelines, and clinical scope |

---

## 9. License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
