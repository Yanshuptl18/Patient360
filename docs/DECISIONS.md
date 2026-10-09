# Patient360: Architectural Decision Records (ADRs)

## ADR-001: Selection of FastAPI for Backend Framework
* **Status:** Accepted
* **Context:** Need a high-performance, asynchronous Python backend with robust typing and automatic API contract generation.
* **Decision:** Adopt FastAPI with Pydantic v2.
* **Consequences:** Native async support, automatic OpenAPI/Swagger generation, strict schema validation, seamless integration with Python AI/NLP libraries.

---

## ADR-002: Selection of React + Vite + TypeScript for Frontend
* **Status:** Accepted
* **Context:** Need a responsive, modern frontend with fast local development cycles and strict type alignment with backend schemas.
* **Decision:** Adopt React 18, Vite, TypeScript, and Tailwind CSS.
* **Consequences:** Near-instant hot module replacement (HMR), compile-time type safety, lightweight bundle size, zero heavy runtime framework overhead.

---

## ADR-003: Selection of PostgreSQL for Relational Persistence
* **Status:** Accepted
* **Context:** Patient records, clinical timelines, document metadata, and audit logs require strict relational integrity and ACID guarantees.
* **Decision:** Use PostgreSQL 16 managed via SQLAlchemy 2.0 and Alembic.
* **Consequences:** Rock-solid data integrity, declarative database migrations, and native JSONB support for dynamic metadata.

---

## ADR-004: Selection of Qdrant as Dedicated Vector Database
* **Status:** Accepted
* **Context:** Vector search requires low RAM overhead on a 16 GB machine while supporting strict pre-filtering by patient ID and tenant.
* **Decision:** Adopt Qdrant running in Docker.
* **Consequences:** High-performance Rust engine with $< 200\text{ MB}$ idle memory usage; native support for payload filtering prior to HNSW search; eliminates cross-patient vector leakage.

---

## ADR-005: Local FastEmbed (`bge-small-en-v1.5`) on CPU
* **Status:** Accepted
* **Context:** External embedding APIs incur recurring token costs and external network latency; large PyTorch models require heavy GPU hardware.
* **Decision:** Use FastEmbed with `BAAI/bge-small-en-v1.5` running via ONNX Runtime on CPU.
* **Consequences:** 100% free local embeddings, 5–15 ms per chunk encoding, $< 250\text{ MB}$ memory footprint, 384-dimensional dense vectors.

---

## ADR-006: In-Memory BM25 for Sparse Keyword Retrieval
* **Status:** Accepted
* **Context:** Clinical records frequently feature specific drug names, abbreviations, and lab codes that dense embeddings miss. Elasticsearch requires 2 GB+ of JVM memory.
* **Decision:** Use in-process BM25 (Rank-BM25) partitioned per patient.
* **Consequences:** Zero JVM memory overhead, ultra-fast exact lexical matching, zero external infrastructure dependencies.

---

## ADR-007: Reciprocal Rank Fusion (RRF) for Hybrid Retrieval
* **Status:** Accepted
* **Context:** Dense vector similarity scores (cosine) and BM25 scores (unbounded BM25 scores) cannot be directly combined via linear addition without calibration.
* **Decision:** Use Reciprocal Rank Fusion with $k=60$ to merge ranked lists.
* **Consequences:** Scale-invariant fusion, superior retrieval accuracy on medical acronyms, predictable candidate ordering.

---

## ADR-008: Pluggable Provider Adapter for LLM Integration
* **Status:** Accepted
* **Context:** Avoiding vendor lock-in; enabling offline testing without live API keys.
* **Decision:** Define abstract `BaseLLMProvider` interface with adapters for Google Gemini, OpenAI, Anthropic Claude, and a high-fidelity `MockLLMProvider`.
* **Consequences:** 100% offline unit/integration testing in CI; flexible switching between hosted providers based on cost, privacy, and performance.

---

## ADR-009: LangGraph State Machine for Bounded Agentic Workflows
* **Status:** Accepted
* **Context:** Need multi-step query decomposition and literature synthesis without dangerous unbounded autonomous loops.
* **Decision:** Implement explicit state graphs via LangGraph with a 5-iteration cap, 30s timeout, read-only tools, and human approval gates.
* **Consequences:** Complete workflow determinism, checkpointing, and human safety oversight.

---

## ADR-010: PyMuPDF (`fitz`) for PDF Extraction
* **Status:** Accepted
* **Context:** Need fast, reliable PDF extraction that tracks exact page numbers and bounding boxes across clinical reports.
* **Decision:** Adopt PyMuPDF.
* **Consequences:** 10–20x faster extraction than Python-only libraries, accurate page-number tracking, robust handling of multi-page reports.

---

## ADR-011: Strict Server-Side Patient Isolation
* **Status:** Accepted
* **Context:** Client-side filtering is insufficient for healthcare privacy; cross-patient data access must be impossible.
* **Decision:** Enforce `patient_id` filters in all SQL queries and Qdrant payload filters at the server service layer.
* **Consequences:** Guaranteed tenant/patient data boundary enforcement.

---

## ADR-012: Deferral of Tesseract OCR to Phase 13
* **Status:** Accepted
* **Context:** Tesseract OCR requires heavy CPU processing, native Windows binary dependencies, and large binary downloads that slow down development of core RAG features.
* **Decision:** Focus on digital PDFs for Phases 1–12; introduce OCR as an optional module in Phase 13.
* **Consequences:** Keeps initial pipeline fast, CPU-friendly, and maintainable.
