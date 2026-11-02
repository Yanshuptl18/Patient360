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
  'What medications are mentioned in the latest discharge summary?',
  'Summarize the laboratory results documented over the last six months.',
  'When was the previous procedure recorded?',
  'Which documents mention the patient\'s reported allergies?',
  'What evidence supports this finding?',
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
        throw new Error(errData.detail || 'We could not complete your search of the medical records.');
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
        setError('We could not complete your inquiry. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const submitFeedback = (rating: 'positive' | 'negative') => {
    setFeedbackRating(rating);
    setIsFeedbackOpen(true);
  };

  const handleSendFeedback = async () => {
    if (!response || !token) return;
    setIsSubmittingFeedback(true);
    try {
      await fetch('/api/v1/rag/feedback', {
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
          issue_type: feedbackRating === 'negative' ? feedbackIssue : undefined,
          comment: feedbackComment.trim() || undefined,
        }),
      });
      setFeedbackSubmitted(feedbackRating);
      setIsFeedbackOpen(false);
    } catch (err) {
      console.warn('Could not record feedback:', err);
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'supported':
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-teal-50 text-teal-800 border border-teal-200">
            Verified Source
          </span>
        );
      case 'partially_supported':
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
            Partially Verified
          </span>
        );
      case 'unsupported':
      default:
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-rose-50 text-rose-800 border border-rose-200">
            Insufficient Evidence
          </span>
        );
    }
  };

  return (
    <div className="rounded-3xl bg-white border border-slate-200 p-6 flex flex-col h-full overflow-hidden shadow-xs text-slate-900">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 shrink-0">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-teal-50 text-teal-700 border border-teal-200">
              <Sparkles className="w-4 h-4" />
            </div>
            <h2 className="text-sm font-bold text-slate-900">Ask About Medical Records</h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-teal-50 text-teal-800 border border-teal-200">
              Page-Anchored
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Patient: <span className="text-teal-800 font-semibold">{patientName}</span> • Answers
            are grounded strictly in verified source records
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
            placeholder="Ask about this patient's findings, medications, procedures, or laboratory results..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 text-xs placeholder-slate-400 focus:outline-none focus:border-teal-600 focus:bg-white transition-colors"
          />

          <div className="flex items-center space-x-1.5 px-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600">
            <span>Evidence Scope:</span>
            <select
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value, 10))}
              className="bg-transparent text-slate-900 font-medium focus:outline-none"
            >
              <option value="3">3 Sources</option>
              <option value="5">5 Sources</option>
              <option value="10">10 Sources</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-5 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs shadow-xs disabled:opacity-50 flex items-center space-x-2 transition-all cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Searching Records...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Ask</span>
              </>
            )}
          </button>
        </div>

        {/* Suggestion Chips */}
        <div className="flex items-center gap-1.5 flex-wrap pt-1">
          <span className="text-[11px] text-slate-500 font-medium">Suggested questions:</span>
          {PRESET_QUERIES.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => setQuery(preset)}
              className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] transition-colors border border-slate-200 cursor-pointer"
            >
              {preset}
            </button>
          ))}
        </div>
      </form>

      {/* Main Output Container */}
      <div className="mt-4 flex-1 overflow-y-auto space-y-4 pr-1">
        {error && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-center space-x-3 text-rose-800 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {!response && !isLoading && !error && (
          <div className="py-16 text-center text-slate-500 flex flex-col items-center justify-center space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-xs font-bold text-slate-700">Medical Records Assistant Ready</h3>
            <p className="text-[11px] text-slate-500 max-w-md">
              Ask about clinical findings, diagnostic tests, or therapy plans. Every synthesized
              statement is anchored with direct page numbers from the patient dossier.
            </p>
          </div>
        )}

        {response && (
          <div className="space-y-4">
            {/* Abstention Banner if no facts found */}
            {response.retrieval_metadata?.is_abstention ? (
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 space-y-2">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-amber-700" />
                  <span className="text-xs font-bold">Insufficient Evidence in Records</span>
                </div>
                <p className="text-xs leading-relaxed">{response.answer}</p>
                <p className="text-[11px] text-amber-800">
                  Patient360 does not generate conclusions not documented in the available medical records.
                </p>
              </div>
            ) : (
              /* Synthesized Answer Card */
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-teal-700" />
                    <span className="text-xs font-bold text-slate-900">Grounded Evidence Summary</span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-slate-500 text-[11px]">Supporting Evidence:</span>
                    <span className="px-2 py-0.5 rounded-full font-bold bg-teal-50 text-teal-800 text-[11px] border border-teal-200">
                      {response.citations.length} cited source{response.citations.length === 1 ? '' : 's'}
                    </span>
                  </div>
                </div>

                <div className="text-xs text-slate-800 leading-relaxed font-sans whitespace-pre-wrap">
                  {response.answer}
                </div>

                {/* Feedback Bar */}
                <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
                  <div className="flex items-center space-x-3">
                    <span>Helpful answer?</span>
                    <button
                      onClick={() => submitFeedback('positive')}
                      disabled={feedbackSubmitted !== null}
                      className={`p-1 rounded-lg transition-colors cursor-pointer ${
                        feedbackSubmitted === 'positive'
                          ? 'bg-teal-100 text-teal-800'
                          : 'hover:bg-slate-200 text-slate-500 hover:text-teal-700'
                      }`}
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => submitFeedback('negative')}
                      disabled={feedbackSubmitted !== null}
                      className={`p-1 rounded-lg transition-colors cursor-pointer ${
                        feedbackSubmitted === 'negative'
                          ? 'bg-rose-100 text-rose-800'
                          : 'hover:bg-slate-200 text-slate-500 hover:text-rose-700'
                      }`}
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                    {feedbackSubmitted && (
                      <span className="text-teal-700 text-[10px] font-semibold">Feedback recorded</span>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 text-slate-400 text-[10px]">
                    <Clock className="w-3 h-3" />
                    <span>Response Time: {response.retrieval_metadata?.total_latency_ms ?? 0}ms</span>
                  </div>
                </div>
              </div>
            )}

            {/* Citations & Evidence Panel */}
            {response.citations.length > 0 && (
              <div className="p-4 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Quote className="w-4 h-4 text-teal-700" />
                    <h3 className="text-xs font-bold text-slate-900">
                      Supporting Document Evidence ({response.citations.length})
                    </h3>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    Click a source below to verify quotation and original PDF page
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
                          ? 'bg-teal-50 border-teal-300 text-slate-900 shadow-xs'
                          : 'bg-slate-50 border-slate-200 hover:border-slate-300 text-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1 mb-1.5">
                        <div className="flex items-center space-x-1.5 overflow-hidden">
                          <FileText className="w-3 h-3 text-teal-700 shrink-0" />
                          <span className="text-xs font-bold truncate text-slate-900">
                            {c.document_title}
                          </span>
                        </div>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-white border border-slate-200 text-slate-700 shrink-0">
                          Page {c.page_number}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-600 truncate max-w-[180px]">{c.claim_text}</span>
                        {getStatusBadge(c.verification_status)}
                      </div>
                    </button>
                  ))}
                </div>

                {/* Selected Citation Inspector */}
                {selectedCitation && (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 mt-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-800">
                      <span>Source Quotation Verification</span>
                      {getStatusBadge(selectedCitation.verification_status)}
                    </div>
                    <div className="p-3 rounded-lg bg-white font-serif text-xs text-slate-900 leading-relaxed border border-slate-200">
                      &quot;{selectedCitation.exact_quote}&quot;
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                      <div>
                        <span>Document: {selectedCitation.document_title}</span>
                        <span className="mx-1.5">•</span>
                        <span>Page: {selectedCitation.page_number}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setIsCitationModalOpen(true)}
                        className="px-3 py-1.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer shadow-xs"
                      >
                        <FileText className="w-3.5 h-3.5 text-teal-700" />
                        <span>Open Document at Source Page</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Limitations Notice */}
            {response.limitations.length > 0 && (
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600 flex items-start space-x-2">
                <HelpCircle className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-semibold text-slate-800">Clinical Notice:</span>
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white border border-slate-200 p-5 space-y-3 shadow-xl text-slate-900">
            <h3 className="text-sm font-bold text-slate-900">
              Submit Quality Rating ({feedbackRating === 'positive' ? 'Helpful' : 'Needs Review'})
            </h3>
            <p className="text-xs text-slate-500">
              Provide optional feedback on accuracy or documentation clarity to help improve clinical retrieval.
            </p>

            {feedbackRating === 'negative' && (
              <div>
                <label className="text-xs text-slate-700 font-medium block mb-1">Issue Category:</label>
                <select
                  value={feedbackIssue}
                  onChange={(e) => setFeedbackIssue(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:border-teal-600"
                >
                  <option value="none">General Inaccuracy</option>
                  <option value="incomplete_evidence">Incomplete Evidence</option>
                  <option value="unsupported_claim">Unsupported Claim</option>
                  <option value="conflicting_dates">Conflicting Event Dates</option>
                </select>
              </div>
            )}

            <div>
              <label className="text-xs text-slate-700 font-medium block mb-1">Comments (Optional):</label>
              <textarea
                value={feedbackComment}
                onChange={(e) => setFeedbackComment(e.target.value)}
                placeholder="Add optional notes for clinical review..."
                rows={3}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:border-teal-600"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setIsFeedbackOpen(false)}
                className="px-3 py-1.5 rounded-lg text-xs text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSendFeedback}
                disabled={isSubmittingFeedback}
                className="px-4 py-1.5 rounded-lg bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs transition-colors"
              >
                {isSubmittingFeedback ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PDF Citation Viewer Modal */}
      {selectedCitation && (
        <PDFCitationViewerModal
          isOpen={isCitationModalOpen}
          onClose={() => setIsCitationModalOpen(false)}
          citation={selectedCitation}
        />
      )}
    </div>
  );
};
