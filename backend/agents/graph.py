"""LangGraph state machine for bounded clinical inquiry workflows."""

import datetime
import logging
import time
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session

from backend.agents.state import AgentWorkflowState
from backend.agents.tools import (
    get_patient_dossier,
    inspect_clinical_contradictions,
    query_longitudinal_timeline,
    search_clinical_evidence,
)
from backend.models.user import User

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def _is_timeout(state: AgentWorkflowState) -> bool:
    start_time = float(state.get("start_time_seconds") or 0.0)
    timeout = float(state.get("timeout_seconds") or 30.0)
    return (time.time() - start_time) > timeout


def _is_limit_reached(state: AgentWorkflowState) -> bool:
    iter_count = int(state.get("iteration_count") or 0)
    max_iters = int(state.get("max_iterations") or 5)
    return iter_count >= max_iters


def build_clinical_agent_graph(db: Session, user: User) -> CompiledStateGraph:
    """
    Constructs and compiles the bounded LangGraph state machine.
    Enforces a strict 5-iteration ceiling, 30s timeout guard, and Human-in-the-Loop review gate.
    """

    def planner_node(state: AgentWorkflowState) -> AgentWorkflowState:
        new_state: AgentWorkflowState = cast(AgentWorkflowState, dict(state))
        steps: list[dict[str, Any]] = list(new_state.get("steps_executed") or [])
        patient_id = str(new_state["patient_id"])
        query = str(new_state["query"])
        start_time = float(new_state.get("start_time_seconds") or time.time())
        timeout = float(new_state.get("timeout_seconds") or 30.0)
        max_iters = int(new_state.get("max_iterations") or 5)
        iter_count = int(new_state.get("iteration_count") or 0)

        if _is_timeout(new_state):
            new_state["status"] = "timeout_exceeded"
            new_state["error_message"] = f"Execution budget of {timeout:.1f}s exceeded."
            return new_state

        if _is_limit_reached(new_state):
            new_state["status"] = "iteration_limit_reached"
            new_state["error_message"] = f"Bounded iteration ceiling of {max_iters} exceeded."
            return new_state

        # Tool 1: Patient Dossier
        dossier = get_patient_dossier(db, user, patient_id)
        new_state["patient_dossier"] = dossier

        plan = [
            f"1. Profile patient baseline: {dossier['full_name']} (MRN: {dossier['mrn_synthetic']})",
            f"2. Hybrid retrieve clinical evidence for inquiry: '{query}'",
            "3. Surface longitudinal events and reconcile clinical contradictions",
            "4. Pause for required Human-in-the-Loop clinician review & certification",
        ]
        new_state["plan"] = plan

        step_idx = len(steps) + 1
        steps.append(
            {
                "step_index": step_idx,
                "node_name": "planner",
                "thought": f"Analyzing clinical query against baseline dossier for patient {dossier['full_name']}.",
                "action_tool": "get_patient_dossier",
                "tool_input": {"patient_id": patient_id},
                "tool_output": dossier,
                "timestamp_iso": _now_iso(),
            }
        )
        new_state["steps_executed"] = steps
        new_state["iteration_count"] = iter_count + 1
        new_state["status"] = "executing"
        new_state["elapsed_seconds"] = round(time.time() - start_time, 2)
        return new_state

    def retrieval_node(state: AgentWorkflowState) -> AgentWorkflowState:
        new_state: AgentWorkflowState = cast(AgentWorkflowState, dict(state))
        steps: list[dict[str, Any]] = list(new_state.get("steps_executed") or [])
        patient_id = str(new_state["patient_id"])
        query = str(new_state["query"])
        start_time = float(new_state.get("start_time_seconds") or time.time())
        timeout = float(new_state.get("timeout_seconds") or 30.0)
        max_iters = int(new_state.get("max_iterations") or 5)
        iter_count = int(new_state.get("iteration_count") or 0)

        if _is_timeout(new_state):
            new_state["status"] = "timeout_exceeded"
            new_state["error_message"] = f"Execution budget of {timeout:.1f}s exceeded."
            return new_state

        if _is_limit_reached(new_state):
            new_state["status"] = "iteration_limit_reached"
            new_state["error_message"] = f"Bounded iteration ceiling of {max_iters} exceeded."
            return new_state

        # Tool 2: Hybrid Clinical Search
        evidence = search_clinical_evidence(
            db=db,
            user=user,
            patient_id=patient_id,
            query=query,
            top_k=5,
        )
        new_state["retrieved_evidence"] = evidence

        step_idx = len(steps) + 1
        steps.append(
            {
                "step_index": step_idx,
                "node_name": "retrieval",
                "thought": f"Executed dense + sparse hybrid RRF search. Retrieved {len(evidence)} evidence chunks.",
                "action_tool": "search_clinical_evidence",
                "tool_input": {"query": query, "top_k": 5},
                "tool_output": [
                    {
                        "chunk_id": item["chunk_id"],
                        "doc_title": item["doc_title"],
                        "page_number": item["page_number"],
                        "score": item["rrf_score"],
                    }
                    for item in evidence
                ],
                "timestamp_iso": _now_iso(),
            }
        )
        new_state["steps_executed"] = steps
        new_state["iteration_count"] = iter_count + 1
        new_state["elapsed_seconds"] = round(time.time() - start_time, 2)
        return new_state

    def reconciliation_node(state: AgentWorkflowState) -> AgentWorkflowState:
        new_state: AgentWorkflowState = cast(AgentWorkflowState, dict(state))
        steps: list[dict[str, Any]] = list(new_state.get("steps_executed") or [])
        patient_id = str(new_state["patient_id"])
        query = str(new_state["query"])
        start_time = float(new_state.get("start_time_seconds") or time.time())
        timeout = float(new_state.get("timeout_seconds") or 30.0)
        max_iters = int(new_state.get("max_iterations") or 5)
        iter_count = int(new_state.get("iteration_count") or 0)

        if _is_timeout(new_state):
            new_state["status"] = "timeout_exceeded"
            new_state["error_message"] = f"Execution budget of {timeout:.1f}s exceeded."
            return new_state

        if _is_limit_reached(new_state):
            new_state["status"] = "iteration_limit_reached"
            new_state["error_message"] = f"Bounded iteration ceiling of {max_iters} exceeded."
            return new_state

        # Tool 3 & 4: Timeline & Contradictions
        timeline_events = query_longitudinal_timeline(db, user, patient_id)
        contradictions = inspect_clinical_contradictions(db, user, patient_id)
        new_state["contradictions_found"] = contradictions

        # Draft Clinical Synthesis
        dossier = new_state.get("patient_dossier") or {}
        patient_name = dossier.get("full_name", "Patient")
        mrn = dossier.get("mrn_synthetic", "N/A")
        primary_cond = dossier.get("primary_condition", "Unspecified")

        evidence = new_state.get("retrieved_evidence") or []

        evidence_summary_lines: list[str] = []
        for i, ev in enumerate(evidence, 1):
            doc = ev.get("doc_title", "Document")
            page = ev.get("page_number", 1)
            content_snippet = (ev.get("content", "")[:220] + "...").replace("\n", " ")
            evidence_summary_lines.append(
                f"- **[{i}] {doc} (p. {page})**: {content_snippet} *(RRF Score: {ev.get('rrf_score', 'N/A')})*"
            )

        evidence_section = (
            "\n".join(evidence_summary_lines)
            if evidence_summary_lines
            else "*No specific document excerpts matched the threshold.*"
        )

        contradiction_lines: list[str] = []
        for c in contradictions:
            sev = str(c.get("severity", "MEDIUM")).upper()
            topic = str(c.get("topic", "Clinical Finding"))
            desc = str(c.get("description", ""))
            rec = str(c.get("resolution_recommendation", ""))
            contradiction_lines.append(
                f"- **[{sev}] {topic}**: {desc}\n  *Actionable Recommendation: {rec}*"
            )

        contra_section = (
            "\n".join(contradiction_lines)
            if contradiction_lines
            else "✅ *No conflicting medical findings detected across historical records.*"
        )

        sample_event_titles = [str(e.get("description", ""))[:30] for e in timeline_events[:3]]
        sample_titles_str = ", ".join(sample_event_titles) if sample_event_titles else "None"

        draft = f"""### Clinical Inquiry Draft Synthesis

**Patient Profile:** {patient_name} | **MRN:** {mrn} | **Condition:** {primary_cond}
**Clinical Inquiry:** {query}

---

#### 1. Grounded Document Evidence
{evidence_section}

---

#### 2. Cross-Document Contradiction Analysis
{contra_section}

---

#### 3. Longitudinal Timeline Observations
- Total extracted longitudinal events: **{len(timeline_events)}**.
- Identified temporal milestones: {sample_titles_str}

---

> ⚠️ **Human-in-the-Loop Review Gate**:
> This synthesized finding requires explicit clinician review and certification prior to permanent diagnostic or treatment recording.
"""
        new_state["draft_synthesis"] = draft

        step_idx = len(steps) + 1
        steps.append(
            {
                "step_index": step_idx,
                "node_name": "reconciliation",
                "thought": (
                    f"Cross-referenced {len(evidence)} evidence chunks with {len(timeline_events)} timeline events. "
                    f"Surfaced {len(contradictions)} potential contradictions. Drafted preliminary synthesis."
                ),
                "action_tool": "inspect_clinical_contradictions",
                "tool_input": {"patient_id": patient_id},
                "tool_output": {
                    "timeline_events_count": len(timeline_events),
                    "contradictions_count": len(contradictions),
                },
                "timestamp_iso": _now_iso(),
            }
        )
        new_state["steps_executed"] = steps
        new_state["iteration_count"] = iter_count + 1
        new_state["status"] = "awaiting_approval"
        new_state["approval_status"] = "pending"
        new_state["elapsed_seconds"] = round(time.time() - start_time, 2)
        return new_state

    def gate_node(state: AgentWorkflowState) -> AgentWorkflowState:
        new_state: AgentWorkflowState = cast(AgentWorkflowState, dict(state))
        steps: list[dict[str, Any]] = list(new_state.get("steps_executed") or [])
        approval_status = new_state.get("approval_status", "pending")
        feedback = new_state.get("clinician_feedback")
        start_time = float(new_state.get("start_time_seconds") or time.time())

        step_idx = len(steps) + 1
        if approval_status == "approved":
            steps.append(
                {
                    "step_index": step_idx,
                    "node_name": "gate",
                    "thought": f"Clinician approval confirmed. Proceeding to certify final clinical report. Feedback: {feedback or 'None provided.'}",
                    "action_tool": None,
                    "tool_input": None,
                    "tool_output": {"decision": "APPROVED", "feedback": feedback},
                    "timestamp_iso": _now_iso(),
                }
            )
        elif approval_status == "rejected":
            new_state["status"] = "rejected"
            steps.append(
                {
                    "step_index": step_idx,
                    "node_name": "gate",
                    "thought": f"Clinician rejected draft synthesis. Halt workflow. Reason/Feedback: {feedback or 'Rejected without feedback.'}",
                    "action_tool": None,
                    "tool_input": None,
                    "tool_output": {"decision": "REJECTED", "feedback": feedback},
                    "timestamp_iso": _now_iso(),
                }
            )
            new_state["error_message"] = feedback or "Draft clinical report rejected by clinician."
        else:
            new_state["status"] = "awaiting_approval"
            steps.append(
                {
                    "step_index": step_idx,
                    "node_name": "gate",
                    "thought": "Draft synthesis ready. Pausing execution at Human-in-the-Loop review gate.",
                    "action_tool": None,
                    "tool_input": None,
                    "tool_output": {"decision": "PAUSED_FOR_REVIEW"},
                    "timestamp_iso": _now_iso(),
                }
            )

        new_state["steps_executed"] = steps
        new_state["elapsed_seconds"] = round(time.time() - start_time, 2)
        return new_state

    def finalizer_node(state: AgentWorkflowState) -> AgentWorkflowState:
        new_state: AgentWorkflowState = cast(AgentWorkflowState, dict(state))
        steps: list[dict[str, Any]] = list(new_state.get("steps_executed") or [])
        draft = str(new_state.get("draft_synthesis") or "")
        feedback = new_state.get("clinician_feedback")
        start_time = float(new_state.get("start_time_seconds") or time.time())
        approved_at = _now_iso()

        certification_banner = f"""# ✅ Certified Clinical Intelligence Report
**Status:** Clinician Certified & Approved
**Certified By User:** `{user.email}` ({user.role.upper()})
**Timestamp:** `{approved_at}`
"""
        if feedback:
            certification_banner += f"**Clinician Addendum / Review Notes:** {feedback}\n"

        new_state["final_report"] = f"{certification_banner}\n{draft}"
        new_state["status"] = "completed"

        step_idx = len(steps) + 1
        steps.append(
            {
                "step_index": step_idx,
                "node_name": "finalizer",
                "thought": "Certified report generated, verified, and locked.",
                "action_tool": None,
                "tool_input": None,
                "tool_output": {"certified_timestamp": approved_at},
                "timestamp_iso": _now_iso(),
            }
        )
        new_state["steps_executed"] = steps
        new_state["elapsed_seconds"] = round(time.time() - start_time, 2)
        return new_state

    def iteration_limit_node(state: AgentWorkflowState) -> AgentWorkflowState:
        new_state: AgentWorkflowState = cast(AgentWorkflowState, dict(state))
        steps: list[dict[str, Any]] = list(new_state.get("steps_executed") or [])
        max_iters = int(new_state.get("max_iterations") or 5)
        start_time = float(new_state.get("start_time_seconds") or time.time())
        new_state["status"] = "iteration_limit_reached"
        new_state["error_message"] = f"Execution halted: Maximum bounded iteration ceiling of {max_iters} reached."

        steps.append(
            {
                "step_index": len(steps) + 1,
                "node_name": "iteration_limit",
                "thought": f"Hard iteration limit ceiling ({max_iters}) reached. Terminating workflow to prevent runaway loop.",
                "action_tool": None,
                "tool_input": None,
                "tool_output": {"limit": max_iters},
                "timestamp_iso": _now_iso(),
            }
        )
        new_state["steps_executed"] = steps
        new_state["elapsed_seconds"] = round(time.time() - start_time, 2)
        return new_state

    def timeout_node(state: AgentWorkflowState) -> AgentWorkflowState:
        new_state: AgentWorkflowState = cast(AgentWorkflowState, dict(state))
        steps: list[dict[str, Any]] = list(new_state.get("steps_executed") or [])
        timeout = float(new_state.get("timeout_seconds") or 30.0)
        start_time = float(new_state.get("start_time_seconds") or time.time())
        new_state["status"] = "timeout_exceeded"
        new_state["error_message"] = f"Execution halted: Time budget of {timeout:.1f}s exceeded."

        steps.append(
            {
                "step_index": len(steps) + 1,
                "node_name": "timeout",
                "thought": f"Execution time budget of {timeout:.1f}s exceeded. Terminating workflow to preserve platform responsiveness.",
                "action_tool": None,
                "tool_input": None,
                "tool_output": {"timeout_seconds": timeout},
                "timestamp_iso": _now_iso(),
            }
        )
        new_state["steps_executed"] = steps
        new_state["elapsed_seconds"] = round(time.time() - start_time, 2)
        return new_state


    # --- Routing functions ---
    def route_from_start(state: AgentWorkflowState) -> str:
        if state.get("status") == "awaiting_approval":
            return "gate"
        return "planner"

    def route_from_planner(state: AgentWorkflowState) -> str:
        if state.get("status") == "timeout_exceeded" or _is_timeout(state):
            return "timeout"
        if state.get("status") == "iteration_limit_reached" or _is_limit_reached(state):
            return "limit"
        return "retrieval"

    def route_from_retrieval(state: AgentWorkflowState) -> str:
        if state.get("status") == "timeout_exceeded" or _is_timeout(state):
            return "timeout"
        if state.get("status") == "iteration_limit_reached" or _is_limit_reached(state):
            return "limit"
        return "reconciliation"

    def route_from_reconciliation(state: AgentWorkflowState) -> str:
        if state.get("status") == "timeout_exceeded" or _is_timeout(state):
            return "timeout"
        if state.get("status") == "iteration_limit_reached" or _is_limit_reached(state):
            return "limit"
        return "gate"

    def route_from_gate(state: AgentWorkflowState) -> str:
        if state.get("approval_status") == "approved":
            return "finalizer"
        return END

    # --- Build graph ---
    builder = StateGraph(AgentWorkflowState)

    builder.add_node("planner", planner_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("reconciliation", reconciliation_node)
    builder.add_node("gate", gate_node)
    builder.add_node("finalizer", finalizer_node)
    builder.add_node("limit", iteration_limit_node)
    builder.add_node("timeout", timeout_node)

    builder.add_conditional_edges(
        START,
        route_from_start,
        {"planner": "planner", "gate": "gate"},
    )
    builder.add_conditional_edges(
        "planner",
        route_from_planner,
        {"retrieval": "retrieval", "limit": "limit", "timeout": "timeout"},
    )
    builder.add_conditional_edges(
        "retrieval",
        route_from_retrieval,
        {"reconciliation": "reconciliation", "limit": "limit", "timeout": "timeout"},
    )
    builder.add_conditional_edges(
        "reconciliation",
        route_from_reconciliation,
        {"gate": "gate", "limit": "limit", "timeout": "timeout"},
    )
    builder.add_conditional_edges(
        "gate",
        route_from_gate,
        {"finalizer": "finalizer", END: END},
    )

    builder.add_edge("finalizer", END)
    builder.add_edge("limit", END)
    builder.add_edge("timeout", END)

    return builder.compile()
