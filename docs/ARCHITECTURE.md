# Patient360: System Architecture Specification

## 1. Architectural Philosophy and Design Principles
Patient360 follows the principles of **Clean Architecture** and **Domain-Driven Design (DDD)**:
1. **Separation of Concerns:** Business logic is decoupled from API controllers, database persistence, and external AI providers.
2. **Dependency Inversion:** High-level policy modules (RAG orchestration, clinical timeline synthesis) depend on abstractions (`BaseLLMProvider`, `BaseEmbeddingProvider`), not vendor implementations.
3. **Stateless API Gateway:** FastAPI route handlers perform authentication, validation, and delegation to domain services, maintaining no internal session state.
4. **Defense in Depth:** Security, tenant isolation, and audit logging are enforced at the service, database, and vector layers.
5. **Deterministic AI Operations:** AI components are bound by deterministic temperature (0.0), token budgets, structural prompts, and post-generation citation validation.

---

## 2. System Architecture Diagram

```mermaid
flowchart TB
    subgraph ClientTier["Client Tier (React 18 + Vite + TypeScript)"]
        UI["Web Dashboard Shell (Tailwind CSS)"]
        PDFComp["Provenance PDF Viewer (Page Anchor Links)"]
        TimeComp["Interactive Clinical Timeline"]
        MatrixComp["Research Evidence Matrix"]
        EvalComp["RAG Evaluation Laboratory"]
    end

    subgraph APIGateway["API Gateway & Security Layer (FastAPI)"]
        RateLimit["Rate Limiter (slowapi)"]
        CORS["CORS & Request Sanitizer"]
        JWTAuth["JWT Authentication Middleware"]
        RBACGuard["RBAC & Tenant Isolation Guard"]
    end

    subgraph DomainServices["Domain Service Layer"]
        PatientService["Patient & Access Service"]
        DocService["Document Management Service"]
        IngestService["Idempotent Ingestion Pipeline"]
        RetrievalService["Hybrid Retrieval Engine (Dense + BM25)"]
        RAGService["Grounded RAG & Citation Verifier"]
        TimelineService["Timeline & Conflict Synthesis Service"]
        ResearchService["Research Literature & Matrix Service"]
        AgentService["Bounded Agent Orchestrator (LangGraph)"]
        AuditService["Append-Only Audit Service"]
    end

    subgraph DataTier["Data Persistence & Search Tier"]
        Postgres[("PostgreSQL 16\n(Users, Metadata, Events, Citations, Audit)")]
        Qdrant[("Qdrant Vector DB\n(FastEmbed 384-dim Vectors + Filters)")]
        BM25[("BM25 In-Memory Index\n(Sparse Keyword Retrieval)")]
        DocStorage[("Document Storage\n(Encrypted Local Storage)")]
    end

    subgraph Adapters["External Infrastructure Adapters"]
        EmbedAdapter["FastEmbed ONNX CPU Adapter"]
        LLMAdapter["Pluggable LLM Provider Adapter\n(OpenAI / Claude / Gemini / Mock)"]
    end

    UI --> APIGateway
    PDFComp --> APIGateway
    TimeComp --> APIGateway
    MatrixComp --> APIGateway
    EvalComp --> APIGateway

    APIGateway --> RateLimit --> CORS --> JWTAuth --> RBACGuard --> DomainServices

    PatientService --> Postgres
    DocService --> DocStorage
    DocService --> Postgres

    IngestService --> DocStorage
    IngestService --> EmbedAdapter
    IngestService --> Qdrant
    IngestService --> BM25
    IngestService --> Postgres

    RetrievalService --> Qdrant
    RetrievalService --> BM25

    RAGService --> RetrievalService
    RAGService --> LLMAdapter
    RAGService --> Postgres

    TimelineService --> RetrievalService
    TimelineService --> LLMAdapter
    TimelineService --> Postgres

    ResearchService --> RetrievalService
    ResearchService --> LLMAdapter
    ResearchService --> Postgres

    AgentService --> RetrievalService
    AgentService --> TimelineService
    AgentService --> LLMAdapter

    DomainServices --> AuditService --> Postgres
```

---

## 3. Core Component Boundaries & Subsystems

### 3.1 Backend Modular Structure
* `backend/core/`: Configuration settings (Pydantic Settings), database engine, logging configuration, security utilities, and base exception handlers.
* `backend/auth/`: JWT credential validation, password hashing, and role permission dependencies.
* `backend/patients/`: Patient demographic CRUD, panel assignments, and authorization verification.
* `backend/documents/`: File upload validation, MIME checking, SHA-256 deduplication, and encrypted local file storage.
* `backend/ingestion/`: Text extraction via PyMuPDF, clinical text normalization, semantic sliding-window chunking, and metadata attribution.
* `backend/embeddings/`: Abstract `BaseEmbeddingProvider` and local CPU FastEmbed implementation.
* `backend/retrieval/`: Qdrant client wrapper, in-memory BM25 lexical index, and Reciprocal Rank Fusion (RRF) algorithm.
* `backend/rag/`: Prompt assembly with delimiter boundaries, abstract `BaseLLMProvider`, response parser, and N-gram citation verifier.
* `backend/timeline/`: Clinical event extraction (Diagnoses, Medications, Encounters, Labs), date reconciliation, and contradiction detection.
* `backend/research/`: Biomedical study parameter extraction, comparative matrix generator, and dossier report exporter.
* `backend/agents/`: LangGraph state machine, tool definitions with explicit authorization schemas, iteration guards, and human approval checkpoints.
* `backend/audit/`: Sanitized, append-only security and operational audit trail.
* `backend/evaluation/`: Automated benchmark test runner, metric calculators (Recall, MRR, Faithfulness, Citation Precision).

---

## 4. End-to-End Pipeline Flows

### 4.1 Document Ingestion Flow
```mermaid
sequenceDiagram
    autonumber
    actor Clinician as Authorized User
    participant Gateway as FastAPI Router
    participant DocSvc as Document Service
    participant Storage as File Storage
    participant Extractor as PyMuPDF Extractor
    participant Chunker as Semantic Chunker
    participant FastEmbed as FastEmbed (CPU)
    participant Qdrant as Qdrant Vector Store
    participant BM25 as BM25 Index
    participant DB as PostgreSQL DB

    Clinician->>Gateway: POST /api/v1/documents/upload (PDF, patient_id)
    Gateway->>DocSvc: Validate file size (<=25MB), magic bytes, SHA-256
    DocSvc->>Storage: Save file to local encrypted disk
    DocSvc->>DB: INSERT INTO documents (status='processing')
    Gateway-->>Clinician: 202 Accepted (document_id)

    DocSvc->>Extractor: Extract text with page numbers & block boundaries
    Extractor->>Chunker: Pass normalized page structures
    Chunker->>Chunker: Split into 512-token chunks (64 overlap)
    Chunker->>DB: INSERT INTO document_chunks

    par Dense Indexing
        Chunker->>FastEmbed: Encode chunks (bge-small-en-v1.5, 384-dim)
        FastEmbed->>Qdrant: Upsert vectors with payload (patient_id, doc_id, page_no)
    and Sparse Indexing
        Chunker->>BM25: Tokenize & update patient BM25 index
    end

    DocSvc->>DB: UPDATE documents (status='completed')
```

### 4.2 Hybrid Retrieval and Grounded RAG Flow
```mermaid
sequenceDiagram
    autonumber
    actor Clinician as Authorized Reviewer
    participant Gateway as FastAPI Router
    participant RAG as RAG Service
    participant Retrieval as Hybrid Engine
    participant Qdrant as Qdrant DB
    participant BM25 as BM25 Index
    participant LLM as LLM Adapter
    participant Verifier as Citation Verifier
    participant DB as PostgreSQL DB

    Clinician->>Gateway: POST /api/v1/rag/query (query, patient_id)
    Gateway->>Gateway: Verify user has permission for patient_id
    Gateway->>RAG: Execute Grounded Q&A

    par Dual Retrieval
        RAG->>Retrieval: Dense Search (patient_id filter) -> Qdrant (Top 20)
    and Lexical Search
        RAG->>Retrieval: Sparse Search (patient_id filter) -> BM25 (Top 20)
    end

    Retrieval->>Retrieval: Reciprocal Rank Fusion (RRF k=60)
    Retrieval->>Retrieval: Deduplicate & select Top 5 chunks
    Retrieval-->>RAG: Ranked Evidence Chunks with Page Provenance

    RAG->>RAG: Assemble Prompt with untrusted data delimiters (<=2000 tokens)
    RAG->>LLM: Generate Grounded Answer (temp=0.0)
    LLM-->>RAG: Answer with [Doc: X, Page Y] citations

    RAG->>Verifier: Parse citations & check claim entailment against chunk text
    Verifier-->>RAG: Verified response, citation status, confidence score
    RAG->>DB: INSERT INTO qa_messages & message_citations
    RAG-->>Gateway: Grounded Response Payload
    Gateway-->>Clinician: 200 OK (Answer + Clickable Citations)
```

---

## 5. Agentic Workflow Architecture

```mermaid
stateDiagram-v2
    [*] --> StartTask: Complex Inquiry Received
    StartTask --> QueryDecomposition: Plan Sub-queries (Max 3)
    
    state BoundedExecution {
        QueryDecomposition --> SelectTool: Choose Read-Only Tool
        SelectTool --> ExecuteTool: Patient or Research Retrieval
        ExecuteTool --> CheckSufficiency: Evaluate Evidence Depth
        CheckSufficiency --> SelectTool: More Info Needed (Iter < 5)
    }

    CheckSufficiency --> SynthesizeFindings: Sufficient Evidence OR Max Iter (5)
    SynthesizeFindings --> DetectContradictions: Surface Conflicting Records
    DetectContradictions --> VerifyCitations: Entailment & Source Match
    
    VerifyCitations --> HumanApprovalGate: Clinician Review Required
    HumanApprovalGate --> ApprovedReport: Clinician Clicks "Approve"
    HumanApprovalGate --> QueryDecomposition: Clinician Requests Re-query
    ApprovedReport --> [*]
```

---

## 6. Deployment and Infrastructure Overview
* **Multi-Container Compose:** Runs PostgreSQL and Qdrant in Docker with resource caps suitable for local Windows 16 GB machines.
* **Local Backend Service:** Python 3.11 virtual environment executing Uvicorn with async worker processes.
* **Local Frontend Service:** Vite dev server executing React 18 with Hot Module Replacement.
* **Production Path:** Multi-stage Docker builds compiling frontend to static assets served via Nginx reverse proxy routing `/api/` to Gunicorn/Uvicorn backend workers.
