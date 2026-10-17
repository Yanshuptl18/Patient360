"""Complete live verification suite for deployed Patient360 Google Cloud Run instance."""

import json
import urllib.request
import urllib.error

BASE_URL = "https://patient360-frontend-442154825091.us-central1.run.app"

def request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        try:
            err_body = json.loads(err.read().decode("utf-8"))
        except Exception:
            err_body = str(err)
        return err.code, err_body
    except Exception as exc:
        return 0, str(exc)

def run_tests():
    print("============================================================")
    print("   PATIENT360 LIVE CLOUD RUN E2E PRODUCTION VERIFICATION   ")
    print("============================================================")
    results = []

    # 1. Health check
    status, body = request("/health")
    print(f"[1] Basic Health Check: Status {status} -> {body}")
    results.append(("Basic Health Check (/health)", status == 200 and body.get("status") == "OK"))

    # 2. Detailed diagnostics check
    status, body = request("/api/v1/health")
    db_status = body.get('components', {}).get('database', {}).get('status')
    vec_status = body.get('components', {}).get('vector_store', {}).get('status')
    llm_status = body.get('components', {}).get('llm_provider', {}).get('status')
    print(f"[2] Diagnostics Health: Status {status} -> {body.get('status')} | DB: {db_status} | Vec: {vec_status} | LLM: {llm_status}")
    results.append(("Diagnostics Health Check (/api/v1/health)", status == 200 and body.get("status") == "HEALTHY"))

    # 3. Doctor Demo Login
    status, login_res = request("/api/v1/auth/demo-login", method="POST", data={"role_key": "doctor"})
    doc_token = login_res.get("access_token") if status == 200 else None
    print(f"[3] Doctor Demo Login: Status {status} -> User: {login_res.get('user', {}).get('email')}")
    results.append(("Doctor Demo Login", status == 200 and bool(doc_token)))

    # 4. Nurse Demo Login
    status, nurse_user = request("/api/v1/auth/demo-login", method="POST", data={"role_key": "nurse"})
    print(f"[4] Nurse Demo Login: Status {status} -> {nurse_user.get('user', {}).get('email')}")
    results.append(("Nurse Demo Login", status == 200 and "access_token" in nurse_user))

    # 5. System Administrator Demo Login
    status, admin_user = request("/api/v1/auth/demo-login", method="POST", data={"role_key": "system_admin"})
    print(f"[5] System Admin Demo Login: Status {status} -> {admin_user.get('user', {}).get('email')}")
    results.append(("System Admin Demo Login", status == 200 and "access_token" in admin_user))

    # 6. Patient Listing
    status, patients = request("/api/v1/patients/", token=doc_token)
    print(f"[6] Patient Listing: Status {status} -> Count: {len(patients) if isinstance(patients, list) else 0}")
    results.append(("Patient Listing (RBAC Doctor)", status == 200 and len(patients) > 0))

    eleanor = next((p for p in patients if p.get("mrn_synthetic") == "SYNTH-10001"), None)
    eleanor_id = eleanor["id"] if eleanor else None

    # 7. Patient Detail & Timeline
    if eleanor_id:
        status, pt = request(f"/api/v1/patients/{eleanor_id}", token=doc_token)
        print(f"[7] Patient Dossier: Status {status} -> Name: {pt.get('first_name')} {pt.get('last_name')}")
        results.append(("Patient Dossier Retrieve", status == 200))

        status, timeline = request(f"/api/v1/timeline/patients/{eleanor_id}", token=doc_token)
        events = timeline.get("events", []) if isinstance(timeline, dict) else []
        contradictions = timeline.get("contradictions", []) if isinstance(timeline, dict) else []
        print(f"[8] Longitudinal Timeline: Status {status} -> Events: {len(events)} | Contradictions: {len(contradictions)}")
        results.append(("Longitudinal Timeline & Contradictions", status == 200 and len(events) > 0))

    # 8. Research Studies
    status, studies = request("/api/v1/research/studies", token=doc_token)
    studies_count = len(studies) if isinstance(studies, list) else 0
    print(f"[9] Research Studies: Status {status} -> Count: {studies_count}")
    results.append(("Research Studies Retrieval", status == 200 and studies_count > 0))

    # 9. Grounded RAG Query with Page-Level Citations
    if eleanor_id:
        rag_payload = {
            "query": "What was Eleanor Vance LVEF on repeat echocardiogram?",
            "patient_id": eleanor_id,
            "top_k": 3
        }
        status, rag_resp = request("/api/v1/rag/query", method="POST", data=rag_payload, token=doc_token)
        answer = rag_resp.get("answer", "") if isinstance(rag_resp, dict) else ""
        citations = rag_resp.get("citations", []) if isinstance(rag_resp, dict) else []
        print(f"[10] Grounded RAG Query: Status {status} -> Answer length: {len(answer)} chars | Citations: {len(citations)}")
        for idx, c in enumerate(citations):
            print(f"     Citation {idx+1}: Doc: '{c.get('document_title')}', Page: {c.get('page_number')}")
        results.append(("Evidence-Grounded RAG with Citations", status == 200 and len(citations) > 0))

    # 10. Unsupported Query returns Insufficient Evidence
    arthur = next((p for p in patients if p.get("mrn_synthetic") == "SYNTH-10004"), None)
    if arthur:
        rag_payload_unsupported = {
            "query": "Does patient have intracranial hemorrhage?",
            "patient_id": arthur["id"],
            "top_k": 3
        }
        status, rag_abstain = request("/api/v1/rag/query", method="POST", data=rag_payload_unsupported, token=doc_token)
        is_abstain = rag_abstain.get("retrieval_metadata", {}).get("is_abstention", False) if isinstance(rag_abstain, dict) else False
        answer_text = rag_abstain.get("answer", "") if isinstance(rag_abstain, dict) else ""
        print(f"[11] Unsupported Query Handling: Status {status} -> Abstention: {is_abstain} | Text: '{answer_text[:40]}...'")
        results.append(("Insufficient-Evidence Guardrail", status == 200 and is_abstain and "Insufficient evidence" in answer_text))

    # 11. Patient Authorization Isolation Test (RBAC Security)
    status, patient_user = request("/api/v1/auth/demo-login", method="POST", data={"role_key": "patient"})
    pt_token = patient_user.get("access_token") if status == 200 else None
    if pt_token and arthur:
        # Patient Eleanor Vance accessing Arthur Dent's dossier must receive 403 Forbidden
        status, pt_access = request(f"/api/v1/patients/{arthur['id']}", token=pt_token)
        print(f"[12] Patient Isolation Test: Status {status} (Expected 403 Forbidden)")
        results.append(("RBAC Patient Isolation Barrier", status == 403))

    print("\n============================================================")
    print("                E2E VERIFICATION REPORT CARD                ")
    print("============================================================")
    all_passed = True
    for name, passed in results:
        flag = "PASSED" if passed else "FAILED"
        if not passed:
            all_passed = False
        print(f"  [{flag}] {name}")
    print("------------------------------------------------------------")
    print(f"FINAL RESULT: {'ALL 12 VERIFICATIONS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    print("============================================================")
    return all_passed

if __name__ == "__main__":
    run_tests()
