"""Integration tests for bounded clinical agent workflow endpoints and RBAC boundaries."""

from fastapi.testclient import TestClient


def test_agent_workflow_full_lifecycle(
    client: TestClient,
    reviewer_headers: dict[str, str],
) -> None:
    """Verifies end-to-end agent workflow execution, telemetry inspection, and clinician approval."""
    # 1. Create patient
    p_resp = client.post(
        "/api/v1/patients",
        headers=reviewer_headers,
        json={
            "mrn_synthetic": "SYNTH-AGT-INT-01",
            "first_name": "Gabriel",
            "last_name": "Monroe",
            "date_of_birth": "1962-07-04",
            "gender": "male",
            "primary_condition": "Type 2 Diabetes Mellitus with Peripheral Neuropathy",
        },
    )
    assert p_resp.status_code == 201
    patient_id = p_resp.json()["id"]

    # 2. Initiate Agent Run
    run_resp = client.post(
        "/api/v1/agents/runs",
        headers=reviewer_headers,
        json={
            "patient_id": patient_id,
            "query": "Synthesize glycemic control and assess medication adherence risks",
            "max_iterations": 5,
        },
    )
    assert run_resp.status_code == 201
    run_data = run_resp.json()
    run_id = run_data["run_id"]

    assert run_data["status"] == "awaiting_approval"
    assert run_data["approval_status"] == "pending"
    assert run_data["iteration_count"] >= 1
    assert run_data["iteration_count"] <= 5
    assert len(run_data["steps"]) >= 3
    assert run_data["draft_synthesis"] is not None
    assert run_data["final_report"] is None

    # Verify telemetry in steps
    step_nodes = [s["node_name"] for s in run_data["steps"]]
    assert "planner" in step_nodes
    assert "retrieval" in step_nodes
    assert "reconciliation" in step_nodes

    # 3. Retrieve Snapshot by run_id
    get_resp = client.get(f"/api/v1/agents/runs/{run_id}", headers=reviewer_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["run_id"] == run_id

    # 4. List Patient Agent Runs
    list_resp = client.get(f"/api/v1/agents/patients/{patient_id}/runs", headers=reviewer_headers)
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert len(runs) >= 1
    assert runs[0]["run_id"] == run_id

    # 5. Clinician Review: Approve with Feedback
    review_resp = client.post(
        f"/api/v1/agents/runs/{run_id}/review",
        headers=reviewer_headers,
        json={
            "approved": True,
            "feedback": "Confirmed laboratory HbA1c trend and agreed with glycemic monitoring plan.",
        },
    )
    assert review_resp.status_code == 200
    review_data = review_resp.json()
    assert review_data["status"] == "completed"
    assert review_data["approval_status"] == "approved"
    assert review_data["final_report"] is not None
    assert "Certified Clinical Intelligence Report" in review_data["final_report"]
    assert "Confirmed laboratory HbA1c trend" in review_data["final_report"]

    # 6. Verify Completed Snapshot
    final_snap = client.get(f"/api/v1/agents/runs/{run_id}", headers=reviewer_headers).json()
    assert final_snap["status"] == "completed"
    assert final_snap["approval_status"] == "approved"


def test_agent_workflow_horizontal_access_boundary(
    client: TestClient,
    reviewer_headers: dict[str, str],
    researcher_headers: dict[str, str],
) -> None:
    """Verifies that cross-tenant / unauthorized personas are blocked with 403 Forbidden."""
    # Reviewer creates patient
    p_resp = client.post(
        "/api/v1/patients",
        headers=reviewer_headers,
        json={
            "mrn_synthetic": "SYNTH-AGT-INT-02",
            "first_name": "Julian",
            "last_name": "Bashir",
            "date_of_birth": "1965-11-12",
            "gender": "male",
            "primary_condition": "Cardiomyopathy",
        },
    )
    assert p_resp.status_code == 201
    patient_id = p_resp.json()["id"]

    # Reviewer starts run
    run_resp = client.post(
        "/api/v1/agents/runs",
        headers=reviewer_headers,
        json={
            "patient_id": patient_id,
            "query": "Review cardiac biomarkers",
        },
    )
    assert run_resp.status_code == 201
    run_id = run_resp.json()["run_id"]

    # Researcher attempts unauthorized run creation -> 403
    unauth_run_resp = client.post(
        "/api/v1/agents/runs",
        headers=researcher_headers,
        json={
            "patient_id": patient_id,
            "query": "Unauthorized attempt",
        },
    )
    assert unauth_run_resp.status_code == 403

    # Researcher attempts unauthorized snapshot access -> 403
    unauth_get_resp = client.get(f"/api/v1/agents/runs/{run_id}", headers=researcher_headers)
    assert unauth_get_resp.status_code == 403

    # Researcher attempts unauthorized listing of patient runs -> 403
    unauth_list_resp = client.get(f"/api/v1/agents/patients/{patient_id}/runs", headers=researcher_headers)
    assert unauth_list_resp.status_code == 403

    # Researcher attempts unauthorized review submission -> 403
    unauth_review_resp = client.post(
        f"/api/v1/agents/runs/{run_id}/review",
        headers=researcher_headers,
        json={"approved": True},
    )
    assert unauth_review_resp.status_code == 403
