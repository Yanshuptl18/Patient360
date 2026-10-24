import React, { useState, useEffect, useCallback } from 'react';
import {
  FileSearch,
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

  // Fetch past investigations for this patient
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
    } catch {
      // Handled silently
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
        throw new Error(errData?.error?.message || 'We could not complete this investigation.');
      }

      const snapshot: AgentRunSnapshot = await res.json();
      setActiveRun(snapshot);
      setRuns((prev) => [snapshot, ...prev]);
      setQuery('');
      setClinicianFeedback('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to complete the clinical investigation.');
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
    <div className="flex flex-col h-full bg-white rounded-2xl border border-slate-200 p-5 shadow-sm overflow-hidden">
      {/* Header and Patient Context */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 gap-3 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-teal-50 text-teal-700 border border-teal-200">
            <FileSearch className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-semibold text-slate-900 tracking-tight">Clinical Research Assistant</h2>
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-teal-50 text-teal-700 border border-teal-200">
                Evidence Review Required
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Patient: <span className="font-semibold text-slate-700">{patientName}</span> • Evidence-grounded multi-step inquiry
            </p>
          </div>
        </div>

        {/* Past Investigations Switcher */}
        {runs.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500">History:</span>
            <select
              value={activeRun?.run_id || ''}
              onChange={(e) => {
                const found = runs.find((r) => r.run_id === e.target.value);
                if (found) setActiveRun(found);
              }}
              className="bg-white border border-slate-200 text-slate-700 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-teal-500"
            >
              {runs.map((r, i) => (
                <option key={r.run_id} value={r.run_id}>
                  #{runs.length - i}: {(r.query || '').slice(0, 32)}... ({r.status ? r.status.replace(/_/g, ' ') : 'pending'})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Split Layout: Inquiry Launcher / Steps & Review */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-5 py-4 overflow-hidden">
        {/* Left Column: Launcher & Telemetry Steps */}
        <div className="lg:col-span-5 flex flex-col h-full overflow-hidden space-y-4">
          {/* Query Launch Form */}
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 shrink-0">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                <span>Start an Investigation</span>
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                Evidence synthesis
              </span>
            </div>

            <form onSubmit={handleLaunchRun} className="space-y-3">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Describe your clinical research question (e.g., assess glycemic control and medication contraindications)..."
                rows={3}
                disabled={isSubmitting}
                className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500 resize-none transition-colors"
              />

              {/* Quick Presets */}
              <div className="flex flex-wrap gap-1.5">
                {PRESET_QUERIES.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setQuery(preset)}
                    className="text-xs px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors cursor-pointer text-left"
                  >
                    {preset}
                  </button>
                ))}
              </div>

              <button
                type="submit"
                disabled={isSubmitting || !query.trim()}
                className="w-full py-2 px-3 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-medium text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Research in progress...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-white" />
                    <span>Start Investigation</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Stepped Progress Inspector */}
          <div className="flex-1 min-h-0 bg-slate-50/50 rounded-xl border border-slate-200 p-4 flex flex-col overflow-hidden">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200 shrink-0">
              <span className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-teal-600" />
                <span>Investigation Steps Completed</span>
              </span>
              {activeRun && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
                  {activeRun.steps.length} steps
                </span>
              )}
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pt-3 pr-1">
              {!activeRun ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 py-8">
                  <Activity className="w-8 h-8 mb-2 text-slate-300" />
                  <p className="text-xs text-slate-600 font-medium">No investigation active.</p>
                  <p className="text-xs text-slate-400 mt-1 max-w-xs">
                    Start an inquiry above to observe completed steps and evidence gathered.
                  </p>
                </div>
              ) : (
                activeRun.steps.map((step: WorkflowStepLog) => {
                  const isExpanded = !!expandedSteps[step.step_index];
                  return (
                    <div
                      key={step.step_index}
                      className="rounded-lg bg-white border border-slate-200 p-3 text-xs shadow-xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-[11px]">
                            {step.step_index}
                          </span>
                          <span className="font-semibold text-teal-800 text-xs">
                            {step.node_name.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => toggleStep(step.step_index)}
                          className="text-slate-400 hover:text-slate-600 transition-colors"
                        >
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      </div>

                      <p className="text-slate-600 mt-1.5 text-xs leading-relaxed">
                        {step.thought}
                      </p>

                      {isExpanded && Boolean(step.tool_input || step.tool_output) && (
                        <div className="mt-2.5 pt-2 border-t border-slate-100 space-y-1.5 font-mono text-[11px]">
                          {Boolean(step.tool_input) && (
                            <div>
                              <span className="text-slate-400 block mb-0.5 font-sans text-xs">Input:</span>
                              <pre className="bg-slate-50 p-2 rounded border border-slate-200 text-slate-700 overflow-x-auto">
                                {JSON.stringify(step.tool_input, null, 2)}
                              </pre>
                            </div>
                          )}
                          {Boolean(step.tool_output) && (
                            <div>
                              <span className="text-slate-400 block mb-0.5 font-sans text-xs">Findings:</span>
                              <pre className="bg-slate-50 p-2 rounded border border-slate-200 text-teal-800 overflow-x-auto max-h-40">
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

        {/* Right Column: Status Banner, Draft Report, Review Gate */}
        <div className="lg:col-span-7 flex flex-col h-full overflow-hidden space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2 shrink-0">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {activeRun ? (
            <div className="flex-1 flex flex-col min-h-0 bg-white rounded-xl border border-slate-200 p-4 overflow-hidden shadow-sm">
              {/* State Header with Meter */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-200 gap-2 shrink-0">
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                      activeRun.status === 'awaiting_approval'
                        ? 'bg-amber-50 text-amber-800 border border-amber-200'
                        : activeRun.status === 'completed'
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                        : activeRun.status === 'rejected'
                        ? 'bg-rose-50 text-rose-800 border border-rose-200'
                        : 'bg-teal-50 text-teal-800 border border-teal-200'
                    }`}
                  >
                    {activeRun.status === 'awaiting_approval'
                      ? 'Review and Approve Findings'
                      : activeRun.status.replace(/_/g, ' ')}
                  </span>
                </div>

                <div className="flex items-center space-x-3 text-xs text-slate-500">
                  <div className="flex items-center space-x-1">
                    <RotateCcw className="w-3.5 h-3.5 text-teal-600" />
                    <span>Steps:</span>
                    <span className="font-semibold text-slate-800">
                      {activeRun.iteration_count} / {activeRun.max_iterations}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5 text-teal-600" />
                    <span>Duration:</span>
                    <span className="font-semibold text-slate-800">{activeRun.elapsed_seconds}s</span>
                  </div>
                </div>
              </div>

              {/* Inquiry Prompt */}
              <div className="py-2.5 border-b border-slate-200 text-xs shrink-0 flex items-center justify-between">
                <div>
                  <span className="text-slate-500">Question: </span>
                  <span className="font-medium text-slate-900">{activeRun.query}</span>
                </div>
                {activeRun.final_report && (
                  <button
                    type="button"
                    onClick={() => copyToClipboard(activeRun.final_report || '')}
                    className="flex items-center space-x-1 text-xs text-teal-600 hover:text-teal-700 transition-colors font-medium"
                  >
                    {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied' : 'Copy Report'}</span>
                  </button>
                )}
              </div>

              {/* Report Body */}
              <div className="flex-1 overflow-y-auto py-3 pr-1 text-xs text-slate-700 leading-relaxed space-y-3">
                {activeRun.final_report ? (
                  <div className="bg-slate-50 rounded-lg p-4 border border-emerald-200 whitespace-pre-wrap text-slate-800 font-sans">
                    {activeRun.final_report}
                  </div>
                ) : activeRun.draft_synthesis ? (
                  <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 whitespace-pre-wrap text-slate-800 font-sans">
                    {activeRun.draft_synthesis}
                  </div>
                ) : (
                  <div className="p-8 text-center text-slate-400">
                    No draft report generated yet.
                  </div>
                )}
              </div>

              {/* Human Review Gate Banner */}
              {activeRun.status === 'awaiting_approval' && (
                <div className="mt-3 p-4 rounded-xl bg-amber-50 border border-amber-200 flex flex-col space-y-3 shrink-0">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="p-1.5 rounded-lg bg-amber-100 text-amber-800">
                        <AlertTriangle className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold text-amber-900">
                          Review and Approve Findings
                        </h4>
                        <p className="text-xs text-slate-600 mt-0.5">
                          Investigation paused. Clinical review is required before final report completion.
                        </p>
                      </div>
                    </div>
                  </div>

                  <input
                    type="text"
                    value={clinicianFeedback}
                    onChange={(e) => setClinicianFeedback(e.target.value)}
                    placeholder="Optional reviewer notes or comments..."
                    disabled={isReviewing}
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-amber-500"
                  />

                  <div className="flex items-center justify-end space-x-3 pt-1">
                    <button
                      type="button"
                      disabled={isReviewing}
                      onClick={() => handleReview(false)}
                      className="px-3.5 py-1.5 rounded-lg bg-white hover:bg-rose-50 text-rose-700 border border-rose-200 text-xs font-medium flex items-center space-x-1.5 transition-colors cursor-pointer disabled:opacity-50"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Reject Findings</span>
                    </button>

                    <button
                      type="button"
                      disabled={isReviewing}
                      onClick={() => handleReview(true)}
                      className="px-4 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer shadow-sm disabled:opacity-50"
                    >
                      {isReviewing ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Approving...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Approve and Finalize Report</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Status footer for completed / rejected */}
              {activeRun.status === 'completed' && (
                <div className="mt-3 p-3 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs shrink-0">
                  <div className="flex items-center space-x-2 text-emerald-800">
                    <ShieldCheck className="w-4 h-4" />
                    <span className="font-semibold">Approved Clinical Evidence Report Finalized</span>
                  </div>
                  <span className="text-xs text-slate-500">
                    Reviewed by {user?.email || 'Authorized Clinician'}
                  </span>
                </div>
              )}

              {activeRun.status === 'rejected' && (
                <div className="mt-3 p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-center justify-between text-xs shrink-0">
                  <div className="flex items-center space-x-2 text-rose-800">
                    <XCircle className="w-4 h-4" />
                    <span className="font-semibold">Findings Rejected by Reviewer</span>
                  </div>
                  {activeRun.clinician_feedback && (
                    <span className="text-xs text-slate-500 italic">
                      "{activeRun.clinician_feedback}"
                    </span>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 bg-slate-50/50 rounded-xl border border-slate-200 p-8 flex flex-col items-center justify-center text-center">
              <FileSearch className="w-10 h-10 text-slate-300 mb-3" />
              <h3 className="text-sm font-semibold text-slate-800">Start an Investigation</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Describe a research question to examine patient records with verified page citations and mandatory review.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
