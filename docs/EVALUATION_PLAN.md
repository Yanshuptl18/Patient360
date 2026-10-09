# Patient360: Evaluation Plan & Benchmarking Methodology

## 1. Evaluation Philosophy
Evaluation is treated as a **first-class product feature**, not an afterthought:
1. **Separation of Concerns:** Retrieval quality is measured independently from answer generation quality.
2. **Deterministic Benchmarks:** A frozen, version-controlled synthetic dataset is used for all automated CI/CD and regression checks.
3. **No Fabricated Scores:** Metrics are only reported after automated execution against verifiable test evidence.
4. **Human Verification:** Automated LLM-as-a-judge or NLI metrics are cross-checked against manually annotated ground truth.

---

## 2. Synthetic Benchmark Dataset Composition (50 Items)

The evaluation suite consists of 50 curated synthetic test items distributed across 6 categories:

| Category | Count | Sample Query / Target | Pass Criteria |
| :--- | :---: | :--- | :--- |
| **1. Single-Document Factual** | 12 | *"What was the peak serum creatinine on 2022-03-10?"* | Golden chunk retrieved in Top 3; exact value extracted with page citation. |
| **2. Multi-Document Longitudinal** | 10 | *"Track ejection fraction measurements across 2020 to 2023."* | All 3 relevant discharge summaries retrieved; values arranged chronologically. |
| **3. Contradictory Records** | 8 | *"What drug allergies are documented for this patient?"* | Retrieves both conflicting notes; states both sides without silent resolution. |
| **4. Unanswerable (Abstention)** | 8 | *"Does the patient have a history of celiac disease?"* | System explicitly abstains: *"Insufficient evidence documented in available records."* |
| **5. Adversarial Injection** | 6 | Adversarial PDF attempting to override prompt rules. | Adversarial instruction ignored; response summarizes factual data safely. |
| **6. Research Literature Matrix** | 6 | *"Compare EMPEROR-Preserved and DELIVER trial endpoints."* | Correct sample sizes, hazard ratios, and study limitations extracted. |

---

## 3. Quantitative Evaluation Metrics & Targets

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                      EVALUATION TARGET PERFORMANCE METRICS                    │
├───────────────────────────────┬───────────────┬───────────────────────────────┤
│ Metric                        │ Minimum Target│ Measurement Method            │
├───────────────────────────────┼───────────────┼───────────────────────────────┤
│ Retrieval Recall@5            │ $\ge 0.85$    │ Golden chunk in top 5 chunks  │
│ Mean Reciprocal Rank (MRR)    │ $\ge 0.75$    │ Reciprocal rank of 1st golden │
│ Generation Faithfulness       │ $\ge 0.85$    │ Claims entailed by retrieved  │
│ Citation Precision            │ $\ge 0.90$    │ Valid citations / total cited │
│ Abstention Accuracy           │ $100\%$       │ Correct abstention on unans.  │
│ Retrieval P95 Latency         │ $\le 1.5\text{s}$ | Hybrid search execution timer│
│ End-to-End P95 Latency        │ $\le 4.0\text{s}$ | Query to final verified answer│
└───────────────────────────────┴───────────────┴───────────────────────────────┘
```

---

## 4. Controlled Retrieval Experiments (Phases 7–8)

During Phases 7 and 8, controlled experiments will measure the quantitative impact of each retrieval tier on the 50-item benchmark:
1. **Experiment A: Dense-Only Vector Retrieval** (FastEmbed + Qdrant).
2. **Experiment B: Sparse-Only Lexical Retrieval** (BM25 keyword search).
3. **Experiment C: Hybrid Fusion (RRF)** (FastEmbed + BM25 + Reciprocal Rank Fusion).

*All observed scores, latencies, and token costs will be recorded in `docs/EVALUATION_PLAN.md` and committed to version control.*

---

## 5. Automated Benchmark Runner (`evaluation/runners/`)
* An automated CLI runner (`python -m evaluation.runners.run_benchmark`) executes the benchmark suite.
* Results are persisted in the `evaluation_runs` database table with Git commit hash and timestamp.
* The frontend **RAG Evaluation Laboratory** renders historical comparison charts across runs.
