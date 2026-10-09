# Patient360: Privacy, Healthcare Safety, and Compliance

## 1. Healthcare Safety Principles
Patient360 is strictly engineered as a **clinical research and record synthesis tool**, not an autonomous medical device or diagnostic instrument:
1. **No Autonomous Prescribing or Diagnosis:** The platform will never formulate diagnostic conclusions, propose clinical treatments, or adjust medication dosages.
2. **Explicit Grounding & Traceability:** Every factual clinical statement must link to an exact passage with source title and page number.
3. **Preservation of Clinical Ambiguity:** When historical records conflict (e.g., conflicting surgery dates or allergy reports), the platform must state both documented facts rather than silently resolving the discrepancy.
4. **Mandatory Abstention:** When documented evidence is insufficient to answer an inquiry, the platform must explicitly state: *"Insufficient evidence documented in available records."* It must never extrapolate or guess.

---

## 2. Mandatory Disclaimers and User Interface Notices
Every user interface screen, generated clinical summary, and exported research dossier must include the following prominent notice:

> **CLINICAL NOTICE:** Patient360 is an informational retrieval and synthesis platform. It is NOT a medical device, diagnostic tool, or clinical prescription system. It does not replace the clinical judgment of licensed healthcare professionals. All citations should be verified against source clinical records prior to taking any clinical action.

---

## 3. Emergency Escalation Detection
The platform monitors query inputs for acute emergency symptoms (e.g., *"severe chest pain", "shortness of breath", "acute anaphylaxis", "sudden weakness or numbness"*). 

When acute signals are detected, the system immediately prepends the response with:
> **EMERGENCY WARNING:** This inquiry contains signals of a potential medical emergency. If this relates to an active patient in distress, immediately activate emergency medical services or follow your institution's acute resuscitation protocol.

---

## 4. Data Privacy & Synthetic Data Standards
To maintain complete safety and prevent compliance exposure:
* **Zero Real PHI in Development & Demos:** All development environments, test cases, and demonstration records exclusively utilize **100% synthetic clinical data** generated via Synthea or de-identified public research databases.
* **De-Identification Checklist (HIPAA Safe Harbor Alignment):** Synthetic records are verified to contain zero real:
  * Names, geographic subdivisions, dates directly linked to real persons.
  * Medical Record Numbers (MRNs), Social Security Numbers, phone/fax numbers.
  * Biometric identifiers or photographic images.
* **Server-Side Data Minimization:** Log files strictly record operational metadata (`user_id`, `patient_id`, `document_id`, `http_status`, `latency_ms`). No clinical notes, search queries, or generated text are recorded in application logs.

---

## 5. Right to Erasure & Data Deletion
In accordance with GDPR and HIPAA data handling principles, when a patient or administrator requests document deletion:
* **Relational Purge:** Cascading deletion removes document records, extracted chunks, clinical events, and citation records.
* **Vector Purge:** Qdrant vectors matching `document_id` are permanently removed from the index.
* **File Purge:** The original binary PDF is unlinked from the local encrypted storage directory.
* **Sparse Index Purge:** BM25 inverted index tokens for the document are pruned.
