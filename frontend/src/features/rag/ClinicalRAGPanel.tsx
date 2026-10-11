import React, { useState } from 'react';
import {
  Sparkles,
  Send,
  Loader2,
  AlertCircle,
  CheckCircle2,
  FileText,
  ThumbsUp,
  ThumbsDown,
  Quote,
  Clock,
  Layers,
  HelpCircle,
} from 'lucide-react';
import { CitationItem, RAGQueryResponse } from '../../types';
import { useAuth } from '../auth/AuthContext';
import { PDFCitationViewerModal } from '../documents/PDFCitationViewerModal';

interface ClinicalRAGPanelProps {
  patientId: string;
  patientName: string;
}

const PRESET_QUERIES = [
  'What EGFR mutation or molecular alterations were identified?',
  'Summarize clinical impression and diagnostic assessment.',
  'What targeted treatments or interventions are recommended?',
  'Does the patient have documented penicillin allergy or anaphylaxis?',
];

export const ClinicalRAGPanel: React.FC<ClinicalRAGPanelProps> = ({
  patientId,
  patientName,
}) => {
  const { token } = useAuth();
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<RAGQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<CitationItem | null>(null);
  const [isCitationModalOpen, setIsCitationModalOpen] = useState(false);

  // Feedback state
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<'positive' | 'negative' | null>(null);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState<'positive' | 'negative'>('positive');
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackIssue, setFeedbackIssue] = useState('none');
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || !token) return;

    setIsLoading(true);
    setError(null);
    setResponse(null);
    setSelectedCitation(null);
    setFeedbackSubmitted(null);

    try {
      const res = await fetch('/api/v1/rag/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: query.trim(),
          patient_id: patientId,
          top_k: topK,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Grounded RAG query failed.');
      }

      const data: RAGQueryResponse = await res.json();
      setResponse(data);
      if (data.citations.length > 0) {
        setSelectedCitation(data.citations[0]);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred during synthesis.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const submitFeedback = async (rating: 'positive' | 'negative') => {
    setFeedbackRating(rating);
    setIsFeedbackOpen(true);
  };

  const handleSendFeedback = async () => {
    if (!response || !token) return;
    setIsSubmittingFeedback(true);
    try {
      const res = await fetch('/api/v1/rag/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          patient_id: patientId,
          query: response.query,
          answer: response.answer,
          rating: feedbackRating,
          issue_type: feedbackIssue !== 'none' ? feedbackIssue : null,
          comment: feedbackComment.trim() || null,
        }),
      });
      if (res.ok) {
        setFeedbackSubmitted(feedbackRating);
        setIsFeedbackOpen(false);
        setFeedbackComment('');
      }
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  const getStatusBadge = (status: CitationItem['verification_status']) => {
    switch (status) {
      case 'supported':
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            Supported
          </span>
        );
      case 'partially_supported':
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
            Partially Supported
          </span>
        );
      case 'unsupported':
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
            Unsupported
          </span>
        );
    }
  };

  return (
    <div className="rounded-3xl bg-slate-900/60 border border-slate-800 p-6 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800 shrink-0">
        <div>
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-teal-500/10 text-teal-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <h2 className="text-sm font-semibold text-white">Evidence-Grounded Clinical Inquiries</h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-teal-500/10 text-teal-400 border border-teal-500/20">
              Objective Determinism
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Verifiable Citations
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Dossier: <span className="text-teal-400 font-medium">{patientName}</span> • Strictly
            evidence-grounded with verified page provenance
          </p>
        </div>
      </div>

      {/* Query Form */}
      <form onSubmit={handleSearch} className="mt-4 flex flex-col gap-2 shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a clinical question about this patient's findings, medications, or pathology..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-sm placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
          />

          <div className="flex items-center space-x-1.5 px-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400">
            <span>Sources:</span>
            <select
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value, 10))}
              className="bg-transparent text-slate-200 font-medium focus:outline-none"
            >
              <option value="3" className="bg-slate-900">3 Top Sources</option>
              <option value="5" className="bg-slate-900">5 Top Sources</option>
              <option value="10" className="bg-slate-900">10 Top Sources</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-semibold text-sm shadow-lg shadow-teal-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-all cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Synthesizing...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Inquire</span>
              </>
            )}
          </button>
        </div>

        {/* Suggestion Chips */}
        <div className="flex items-center gap-1.5 flex-wrap pt-1">
          <span className="text-[11px] text-slate-500 font-medium">Try:</span>
          {PRESET_QUERIES.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => {
                setQuery(preset);
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-teal-300 text-[11px] transition-colors border border-slate-700/50 cursor-pointer"
            >
              {preset}
            </button>
          ))}
        </div>
      </form>

      {/* Main Output Container */}
      <div className="mt-4 flex-1 overflow-y-auto space-y-4 pr-1">
        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center space-x-3 text-rose-400 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!response && !isLoading && !error && (
          <div className="py-16 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-slate-800/40 border border-slate-800 flex items-center justify-center text-slate-400">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="max-w-md">
              <h3 className="text-sm font-medium text-slate-300 mb-1">Grounded Clinical Q&A Ready</h3>
              <p className="text-xs text-slate-500">
                Inquire about clinical findings, diagnostic tests, or therapy plans. Every synthesized
                sentence will be anchored by page-level citations from the patient dossier.
              </p>
            </div>
          </div>
        )}

        {response && (
          <div className="space-y-4">
            {/* Abstention Banner if no facts found */}
            {response.retrieval_metadata.is_abstention ? (
              <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 space-y-2">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                  <span className="text-xs font-semibold">Deterministic Abstention Notice</span>
                </div>
                <p className="text-xs leading-relaxed">{response.answer}</p>
                <p className="text-[11px] text-amber-400/80">
                  Patient360 will not hallucinate facts unmentioned in available documentation.
                </p>
              </div>
            ) : (
              /* Synthesized Answer Card */
              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-semibold text-white">Synthesized Clinical Answer</span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-slate-400 text-[11px]">Confidence:</span>
                    <span className="px-2 py-0.5 rounded-full font-bold bg-emerald-500/15 text-emerald-400 text-[11px] border border-emerald-500/30">
                      {(response.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className="text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-wrap">
                  {response.answer}
                </div>

                {/* Feedback Bar */}
                <div className="pt-2 border-t border-slate-800/40 flex items-center justify-between text-[11px] text-slate-400">
                  <div className="flex items-center space-x-3">
                    <span>Rate synthesis accuracy:</span>
                    <button
                      onClick={() => submitFeedback('positive')}
                      disabled={feedbackSubmitted !== null}
                      className={`p-1 rounded-lg transition-colors cursor-pointer ${
                        feedbackSubmitted === 'positive'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'hover:bg-slate-800 text-slate-400 hover:text-emerald-400'
                      }`}
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => submitFeedback('negative')}
                      disabled={feedbackSubmitted !== null}
                      className={`p-1 rounded-lg transition-colors cursor-pointer ${
                        feedbackSubmitted === 'negative'
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'hover:bg-slate-800 text-slate-400 hover:text-rose-400'
                      }`}
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                    {feedbackSubmitted && (
                      <span className="text-emerald-400 text-[10px]">Feedback recorded</span>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 text-slate-500 text-[10px]">
                    <Clock className="w-3 h-3" />
                    <span>Response Time: {response.retrieval_metadata.total_latency_ms}ms</span>
                    <span>•</span>
                    <Layers className="w-3 h-3" />
                    <span>Verified Sources: {response.retrieval_metadata.merged_candidates_count}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Citations & Evidence Panel */}
            {response.citations.length > 0 && (
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Quote className="w-4 h-4 text-teal-400" />
                    <h3 className="text-xs font-semibold text-white">
                      Verified Document Citations ({response.citations.length})
                    </h3>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    Click a citation to inspect excerpt
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {response.citations.map((c, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setSelectedCitation(c)}
                      className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                        selectedCitation?.exact_quote === c.exact_quote
                          ? 'bg-teal-500/10 border-teal-500/50 text-slate-200'
                          : 'bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1 mb-1.5">
                        <div className="flex items-center space-x-1.5 overflow-hidden">
                          <FileText className="w-3 h-3 text-teal-400 shrink-0" />
                          <span className="text-xs font-semibold truncate text-white">
                            {c.document_title}
                          </span>
                        </div>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-teal-500/15 text-teal-300 shrink-0">
                          Page {c.page_number}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-400 truncate max-w-[180px]">{c.claim_text}</span>
                        {getStatusBadge(c.verification_status)}
                      </div>
                    </button>
                  ))}
                </div>

                {/* Selected Citation Inspector */}
                {selectedCitation && (
                  <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2 mt-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                      <span>Source Excerpt Verification</span>
                      {getStatusBadge(selectedCitation.verification_status)}
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-950 font-mono text-[11px] text-teal-300 leading-relaxed border border-slate-800/80">
                      &quot;{selectedCitation.exact_quote}&quot;
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                      <div>
                        <span>Document: {selectedCitation.document_title}</span>
                        <span className="mx-1.5">•</span>
                        <span>Physical Page: {selectedCitation.page_number}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setIsCitationModalOpen(true)}
                        className="px-3 py-1.5 rounded-lg bg-teal-500/15 hover:bg-teal-500/25 text-teal-300 border border-teal-500/30 text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer shadow-sm shadow-teal-500/10"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Open In-Viewer PDF Provenance</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Limitations Notice */}
            {response.limitations.length > 0 && (
              <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 text-[11px] text-slate-400 flex items-start space-x-2">
                <HelpCircle className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-semibold text-slate-300">Clinical Notice & Limitations:</span>
                  {response.limitations.map((lim, i) => (
                    <p key={i}>{lim}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Clinician Feedback Modal */}
      {isFeedbackOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 p-5 space-y-3">
            <h3 className="text-sm font-semibold text-white">
              Submit Quality Rating ({feedbackRating === 'positive' ? 'Positive' : 'Negative'})
            </h3>
            <p className="text-xs text-slate-400">
              Provide optional qualitative notes or flag issues to help calibrate retrieval models.
            </p>

            {feedbackRating === 'negative' && (
              <div>
                <label className="text-xs text-slate-300 font-medium block mb-1">Issue Category:</label>
                <select
                  value={feedbackIssue}
                  onChange={(e) => setFeedbackIssue(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-teal-500"
                >
                  <option value="none">General Critique</option>
                  <option value="hallucination">Hallucination / Unsupported Claim</option>
                  <option value="contradiction_unnoticed">Contradiction Unnoticed</option>
                  <option value="missing_source">Source Document Incomplete</option>
                </select>
              </div>
            )}

            <div>
              <label className="text-xs text-slate-300 font-medium block mb-1">Clinician Notes:</label>
              <textarea
                value={feedbackComment}
                onChange={(e) => setFeedbackComment(e.target.value)}
                placeholder="Describe why this synthesis was accurate or where it fell short..."
                rows={3}
                className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setIsFeedbackOpen(false)}
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSendFeedback}
                disabled={isSubmittingFeedback}
                className="px-4 py-1.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-semibold cursor-pointer"
              >
                {isSubmittingFeedback ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* In-Viewer PDF Citation Provenance Modal */}
      <PDFCitationViewerModal
        isOpen={isCitationModalOpen}
        onClose={() => setIsCitationModalOpen(false)}
        citation={selectedCitation}
      />
    </div>
  );
};
