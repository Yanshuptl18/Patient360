# Patient360: Known Limitations and Technical Boundaries

## 1. Scope & Architectural Boundaries

### 1.1 Non-Clinical Diagnostic Boundary
* Patient360 is an **informational synthesis and evidence retrieval platform**. It is NOT a clinical decision support system, autonomous diagnostic engine, or therapeutic recommendation tool.
* Model-generated outputs must never be treated as clinical ground truth without direct physician review of source records.

### 1.2 Digital PDF Parsing Limitation (Phases 1–12)
* The extraction pipeline relies on PyMuPDF and processes **digital/selectable text PDFs**.
* Scanned, handwritten, or low-resolution image PDFs without OCR text layers are not parsed in Phases 1–12. Optical Character Recognition (Tesseract OCR) is scheduled as an optional module in Phase 13.

### 1.3 Local CPU Hardware Boundaries
* System architecture is strictly designed for local development on a **Windows machine with 16 GB RAM and no dedicated GPU**.
* Large local LLMs (e.g., Llama-3-70B) cannot be run locally. The platform utilizes lightweight CPU dense embeddings (FastEmbed `bge-small-en-v1.5`, 384 dimensions) and hosted API adapters (or a deterministic local Mock) for LLM generation.

### 1.4 Context Window & Retrieval Token Budget
* To guarantee predictable latency, prevent attention distraction, and control API costs, retrieved context is bounded to **2,000 tokens** (typically Top 5 ranked chunks). Queries requiring comprehensive synthesis across hundreds of pages in a single turn rely on agentic query decomposition.

### 1.5 Temporal Reasoning Approximations
* Clinical event extraction relies on regular expressions and LLM-assisted zero-shot extraction. Complex relative temporal expressions (*"two weeks prior to the second recurrence"*) are tagged with `event_date_precision: "approximate"` when an absolute calendar date cannot be resolved.

### 1.6 Synthetic Data Nature
* All development, testing, and demonstration cohorts are synthetic (derived from Synthea or public de-identified datasets). While structurally realistic, synthetic datasets cannot capture every real-world clinical nuance or EHR documentation idiosyncrasy.
