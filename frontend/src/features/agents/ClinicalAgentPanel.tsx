import React, { useState, useEffect, useCallback } from 'react';
import {
  Bot,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  RotateCcw,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Activity,
  ShieldCheck,
  Sparkles,
  Terminal,
  Loader2,
  Copy,
  Check,
} from 'lucide-react';

import {
  AgentRunSnapshot,
  WorkflowStepLog,
} from '../../types';
import { useAuth } from '../auth/AuthContext';

interface ClinicalAgentPanelProps {
  patientId: string;
  patientName: string;
}

const PRESET_QUERIES = [
  'Synthesize glycemic control and medication contraindications',
  'Analyze cardiac biomarkers and reconcile longitudinal findings',
  'Inspect documented allergies and potential drug conflicts',
  'Compile comprehensive cross-document timeline trajectory',
];

export const ClinicalAgentPanel: React.FC<ClinicalAgentPanelProps> = ({
  patientId,
  patientName,
}) => {
  const { token, user } = useAuth();
  const [runs, setRuns] = useState<AgentRunSnapshot[]>([]);
  const [activeRun, setActiveRun] = useState<AgentRunSnapshot | null>(null);
  const [query, setQuery] = useState('');
  const [maxIterations] = useState(5);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const [clinicianFeedback, setClinicianFeedback] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({});
  const [copied, setCopied] = useState(false);

  // Fetch past runs for this patient
  const fetchPatientRuns = useCallback(async () => {
    if (!patientId || !token) return;
    try {
      const res = await fetch(`/api/v1/agents/patients/${patientId}/runs`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data: AgentRunSnapshot[] = await res.json();
        setRuns(data);
        if (data.length > 0 && !activeRun) {
          setActiveRun(data[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load agent runs:', err);
    }
  }, [patientId, token, activeRun]);

  useEffect(() => {
    fetchPatientRuns();
  }, [fetchPatientRuns]);

  const handleLaunchRun = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || isSubmitting || !token) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const res = await fetch('/api/v1/agents/runs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          patient_id: patientId,
          query: query.trim(),
          max_iterations: maxIterations,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData?.error?.message || 'Failed to execute agent workflow.');
      }

      const snapshot: AgentRunSnapshot = await res.json();
      setActiveRun(snapshot);
      setRuns((prev) => [snapshot, ...prev]);
      setQuery('');
      setClinicianFeedback('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown error during workflow execution.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReview = async (approved: boolean) => {
    if (!activeRun || isReviewing || !token) return;

    setIsReviewing(true);
    setError(null);

    try {
      const res = await fetch(`/api/v1/agents/runs/${activeRun.run_id}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          approved,
          feedback: clinicianFeedback.trim() || null,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData?.error?.message || 'Review submission failed.');
      }

      // Re-fetch updated snapshot
      const snapRes = await fetch(`/api/v1/agents/runs/${activeRun.run_id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (snapRes.ok) {
        const updatedSnap: AgentRunSnapshot = await snapRes.json();
        setActiveRun(updatedSnap);
        setRuns((prev) => prev.map((r) => (r.run_id === updatedSnap.run_id ? updatedSnap : r)));
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Review action failed.');
    } finally {
      setIsReviewing(false);
    }
  };

  const toggleStep = (idx: number) => {
    setExpandedSteps((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 rounded-3xl border border-slate-800 p-5 shadow-2xl overflow-hidden">
      {/* Header & Patient Context */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-2xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-bold text-white tracking-tight">Bounded Clinical Agent</h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                LangGraph State Machine
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Subject: <span className="font-semibold text-slate-200">{patientName}</span> • Read-only tools • Hard 5-loop ceiling
            </p>
          </div>
        </div>

        {/* Past Runs Switcher */}
        {runs.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-[11px] text-slate-400">Run History:</span>
            <select
              value={activeRun?.run_id || ''}
              onChange={(e) => {
                const found = runs.find((r) => r.run_id === e.target.value);
                if (found) setActiveRun(found);
              }}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl px-2.5 py-1.5 focus:outline-none focus:border-teal-500"
            >
              {runs.map((r, i) => (
                <option key={r.run_id} value={r.run_id}>
                  #{runs.length - i}: {r.query.slice(0, 32)}... ({r.status})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Split Layout: Inquiry Launcher / Telemetry & Review */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-5 py-4 overflow-hidden">
        {/* Left Column: Launcher & Telemetry Steps (5 cols) */}
        <div className="lg:col-span-5 flex flex-col h-full overflow-hidden space-y-4">
          {/* Query Launch Form */}
          <div className="bg-slate-950/70 rounded-2xl border border-slate-800 p-4 shrink-0 shadow-inner">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-teal-400" />
                <span>New Multi-Step Inquiry</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                Max 5 Loops • 30s Budget
              </span>
            </div>

            <form onSubmit={handleLaunchRun} className="space-y-3">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter clinical inquiry (e.g. assess glycemic control and medication contraindications)..."
                rows={3}
                disabled={isSubmitting}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-teal-500 resize-none transition-colors"
              />

              {/* Quick Presets */}
              <div className="flex flex-wrap gap-1.5">
                {PRESET_QUERIES.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setQuery(preset)}
                    className="text-[10px] px-2 py-0.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700/60 transition-colors cursor-pointer text-left"
                  >
                    {preset}
                  </button>
                ))}
              </div>

              <button
                type="submit"
                disabled={isSubmitting || !query.trim()}
                className="w-full py-2 px-3 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer shadow-lg shadow-teal-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Executing LangGraph State Machine...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-slate-950" />
                    <span>Launch Bounded Clinical Workflow</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Stepped Telemetry Inspector */}
          <div className="flex-1 min-h-0 bg-slate-950/70 rounded-2xl border border-slate-800 p-4 flex flex-col overflow-hidden">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/80 shrink-0">
              <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                <Terminal className="w-3.5 h-3.5 text-indigo-400" />
                <span>Execution Telemetry Trace</span>
              </span>
              {activeRun && (
                <span className="text-[10px] font-mono text-slate-400">
                  {activeRun.steps.length} discrete steps logged
                </span>
              )}
            </div>

            <div className="flex-1 overflow-y-auto space-y-2.5 pt-3 pr-1">
              {!activeRun ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 py-8">
                  <Activity className="w-8 h-8 mb-2 text-slate-600" />
                  <p className="text-xs">No active workflow run selected.</p>
                  <p className="text-[11px] text-slate-600 mt-1">
                    Launch a clinical query above to observe real-time tool calls and state transitions.
                  </p>
                </div>
              ) : (
                activeRun.steps.map((step: WorkflowStepLog) => {
                  const isExpanded = !!expandedSteps[step.step_index];
                  return (
                    <div
                      key={step.step_index}
                      className="rounded-xl bg-slate-900/90 border border-slate-800/90 p-3 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center font-mono text-[10px] font-bold">
                            {step.step_index}
                          </span>
                          <span className="font-semibold text-teal-300 uppercase tracking-wider text-[10px]">
                            {step.node_name}
                          </span>
                          {step.action_tool && (
                            <span className="px-1.5 py-0.2 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[10px] font-mono">
                              {step.action_tool}
                            </span>
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={() => toggleStep(step.step_index)}
                          className="text-slate-400 hover:text-white transition-colors"
                        >
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      </div>

                      <p className="text-slate-300 mt-2 text-[11px] leading-relaxed">
                        {step.thought}
                      </p>

                      {isExpanded && Boolean(step.tool_input || step.tool_output) && (
                        <div className="mt-2.5 pt-2 border-t border-slate-800 space-y-1.5 font-mono text-[10px]">
                          {Boolean(step.tool_input) && (
                            <div>
                              <span className="text-slate-500 block mb-0.5">Input:</span>
                              <pre className="bg-slate-950 p-2 rounded-lg text-slate-300 overflow-x-auto">
                                {JSON.stringify(step.tool_input, null, 2)}
                              </pre>
                            </div>
                          )}
                          {Boolean(step.tool_output) && (
                            <div>
                              <span className="text-slate-500 block mb-0.5">Output:</span>
                              <pre className="bg-slate-950 p-2 rounded-lg text-teal-300/90 overflow-x-auto max-h-40">
                                {JSON.stringify(step.tool_output, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}

                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Column: State Banner, Draft Synthesis / Final Report, Review Gate (7 cols) */}
        <div className="lg:col-span-7 flex flex-col h-full overflow-hidden space-y-4">
          {error && (
            <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2 shrink-0">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {activeRun ? (
            <div className="flex-1 flex flex-col min-h-0 bg-slate-950/70 rounded-2xl border border-slate-800 p-4 overflow-hidden">
              {/* Observable State Header with Iteration Meter */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2 shrink-0">
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2.5 py-1 rounded-xl text-xs font-bold uppercase tracking-wider ${
                      activeRun.status === 'awaiting_approval'
                        ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        : activeRun.status === 'completed'
                        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                        : activeRun.status === 'rejected'
                        ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                        : 'bg-teal-500/15 text-teal-300 border border-teal-500/30'
                    }`}
                  >
                    {activeRun.status.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    ID: {activeRun.run_id}
                  </span>
                </div>

                {/* Meter Gauges */}
                <div className="flex items-center space-x-4 text-xs font-mono">
                  <div className="flex items-center space-x-1.5">
                    <RotateCcw className="w-3.5 h-3.5 text-teal-400" />
                    <span className="text-slate-400">Loops:</span>
                    <span className="font-bold text-white">
                      {activeRun.iteration_count} / {activeRun.max_iterations}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <Clock className="w-3.5 h-3.5 text-cyan-400" />
                    <span className="text-slate-400">Elapsed:</span>
                    <span className="font-bold text-white">{activeRun.elapsed_seconds}s</span>
                  </div>
                </div>
              </div>

              {/* Inquiry Prompt Display */}
              <div className="py-2.5 border-b border-slate-800/80 text-xs shrink-0 flex items-center justify-between">
                <div>
                  <span className="text-slate-500">Inquiry: </span>
                  <span className="font-medium text-slate-200">{activeRun.query}</span>
                </div>
                {activeRun.final_report && (
                  <button
                    type="button"
                    onClick={() => copyToClipboard(activeRun.final_report || '')}
                    className="flex items-center space-x-1 text-[11px] text-teal-400 hover:text-teal-300 transition-colors"
                  >
                    {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied' : 'Copy Report'}</span>
                  </button>
                )}
              </div>

              {/* Report Body View: Final Certified or Draft Synthesis */}
              <div className="flex-1 overflow-y-auto py-3 pr-1 text-xs text-slate-300 leading-relaxed font-sans space-y-3">
                {activeRun.final_report ? (
                  <div className="bg-slate-900/60 rounded-xl p-4 border border-emerald-500/20 whitespace-pre-wrap font-sans text-slate-200">
                    {activeRun.final_report}
                  </div>
                ) : activeRun.draft_synthesis ? (
                  <div className="bg-slate-900/40 rounded-xl p-4 border border-slate-800 whitespace-pre-wrap font-sans text-slate-200">
                    {activeRun.draft_synthesis}
                  </div>
                ) : (
                  <div className="p-8 text-center text-slate-500">
                    No report draft generated yet.
                  </div>
                )}
              </div>

              {/* Human-in-the-Loop Clinician Review Gate Banner */}
              {activeRun.status === 'awaiting_approval' && (
                <div className="mt-3 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex flex-col space-y-3 shrink-0 shadow-lg shadow-amber-500/5">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-300">
                        <AlertTriangle className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-amber-300">
                          Human-in-the-Loop Clinician Review Gate
                        </h4>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          Autonomous workflow paused. Clinician certification required before final report delivery.
                        </p>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300">
                      FR-AGT-04 Gated
                    </span>
                  </div>

                  <input
                    type="text"
                    value={clinicianFeedback}
                    onChange={(e) => setClinicianFeedback(e.target.value)}
                    placeholder="Optional clinician review feedback or certification addendum..."
                    disabled={isReviewing}
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400"
                  />

                  <div className="flex items-center justify-end space-x-3 pt-1">
                    <button
                      type="button"
                      disabled={isReviewing}
                      onClick={() => handleReview(false)}
                      className="px-3.5 py-1.5 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 text-xs font-semibold flex items-center space-x-1.5 transition-colors cursor-pointer disabled:opacity-50"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Reject Synthesis</span>
                    </button>

                    <button
                      type="button"
                      disabled={isReviewing}
                      onClick={() => handleReview(true)}
                      className="px-4 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold flex items-center space-x-1.5 transition-all cursor-pointer shadow-md shadow-emerald-500/20 disabled:opacity-50"
                    >
                      {isReviewing ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Certifying...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Approve & Certify Report</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Status footer for completed / rejected */}
              {activeRun.status === 'completed' && (
                <div className="mt-3 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between text-xs shrink-0">
                  <div className="flex items-center space-x-2 text-emerald-300">
                    <ShieldCheck className="w-4 h-4" />
                    <span className="font-semibold">Certified Clinical Intelligence Report Locked</span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Audited by {user?.email || 'Clinician'}
                  </span>
                </div>
              )}

              {activeRun.status === 'rejected' && (
                <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-between text-xs shrink-0">
                  <div className="flex items-center space-x-2 text-rose-300">
                    <XCircle className="w-4 h-4" />
                    <span className="font-semibold">Synthesis Rejected by Clinician</span>
                  </div>
                  {activeRun.clinician_feedback && (
                    <span className="text-[11px] text-slate-400 italic">
                      "{activeRun.clinician_feedback}"
                    </span>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 bg-slate-950/70 rounded-2xl border border-slate-800 p-8 flex flex-col items-center justify-center text-center">
              <Bot className="w-12 h-12 text-slate-700 mb-3" />
              <h3 className="text-sm font-semibold text-white">Bounded Clinical Inquiry</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm">
                Formulate an inquiry on the left to invoke the LangGraph bounded state machine with hybrid retrieval and human certification gates.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
