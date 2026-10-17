import React, { useState, useEffect, useCallback } from 'react';
import {
  Clock,
  AlertTriangle,
  FileText,
  RefreshCw,
  Loader2,
  CheckCircle2,
  AlertOctagon,
  ChevronDown,
  ChevronUp,
  Activity,
  Pill,
  Stethoscope,
  Scissors,
  FlaskConical,
  ShieldAlert,
} from 'lucide-react';
import {
  ClinicalEvent,
  ClinicalEventType,
  PatientTimelineResponse,
  CitationItem,
} from '../../types';
import { useAuth } from '../auth/AuthContext';
import { PDFCitationViewerModal } from '../documents/PDFCitationViewerModal';

interface ClinicalTimelinePanelProps {
  patientId: string;
  patientName: string;
}

export const ClinicalTimelinePanel: React.FC<ClinicalTimelinePanelProps> = ({
  patientId,
  patientName,
}) => {
  const { token } = useAuth();
  const [timelineData, setTimelineData] = useState<PatientTimelineResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedType, setSelectedType] = useState<ClinicalEventType | 'all'>('all');
  const [onlyContradictions, setOnlyContradictions] = useState(false);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [expandedContradictions, setExpandedContradictions] = useState(true);

  // PDF Citation Inspector Modal
  const [citationForModal, setCitationForModal] = useState<CitationItem | null>(null);
  const [isCitationModalOpen, setIsCitationModalOpen] = useState(false);

  const fetchTimeline = useCallback(async () => {
    if (!patientId || !token) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/v1/timeline/patients/${patientId}?order=${sortOrder}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error?.message || 'We could not load the medical timeline.');
      }
      const data: PatientTimelineResponse = await res.json();
      setTimelineData(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while loading the timeline.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [patientId, sortOrder, token]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  const handleExtractTimeline = async () => {
    if (!patientId || !token) return;
    setIsExtracting(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/timeline/patients/${patientId}/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ patient_id: patientId, force_reextract: true }),
      });
      if (!res.ok) {
        throw new Error('Could not identify events in medical documents.');
      }
      await fetchTimeline();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setIsExtracting(false);
    }
  };

  const handleOpenCitation = (ev: ClinicalEvent) => {
    setCitationForModal({
      document_id: ev.document_id,
      document_title: ev.document_title || 'Document Record',
      page_number: ev.page_number || 1,
      exact_quote: ev.exact_quote || ev.description,
      claim_text: ev.description,
      verification_status: ev.contradiction_flag ? 'unsupported' : 'supported',
    });
    setIsCitationModalOpen(true);
  };

  const getEventIcon = (type: ClinicalEventType) => {
    switch (type) {
      case 'diagnosis':
        return <Activity className="w-3.5 h-3.5 text-teal-700" />;
      case 'medication':
        return <Pill className="w-3.5 h-3.5 text-emerald-700" />;
      case 'procedure':
        return <Scissors className="w-3.5 h-3.5 text-blue-700" />;
      case 'lab_result':
        return <FlaskConical className="w-3.5 h-3.5 text-amber-700" />;
      case 'allergy':
        return <ShieldAlert className="w-3.5 h-3.5 text-rose-700" />;
      case 'encounter':
      default:
        return <Stethoscope className="w-3.5 h-3.5 text-purple-700" />;
    }
  };

  const getEventBadgeClass = (type: ClinicalEventType) => {
    switch (type) {
      case 'diagnosis':
        return 'bg-teal-50 text-teal-800 border-teal-200';
      case 'medication':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'procedure':
        return 'bg-blue-50 text-blue-800 border-blue-200';
      case 'lab_result':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'allergy':
        return 'bg-rose-50 text-rose-800 border-rose-200';
      case 'encounter':
      default:
        return 'bg-purple-50 text-purple-800 border-purple-200';
    }
  };

  const getPrecisionBadge = (prec: ClinicalEvent['event_date_precision']) => {
    switch (prec) {
      case 'day':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-teal-50 text-teal-800 border border-teal-200">
            Exact Date
          </span>
        );
      case 'month':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-blue-50 text-blue-800 border border-blue-200">
            Month Level
          </span>
        );
      case 'year':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-purple-50 text-purple-800 border border-purple-200">
            Year Level
          </span>
        );
      case 'approximate':
      default:
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-50 text-amber-800 border border-amber-200">
            Approximate Date
          </span>
        );
    }
  };

  const filteredEvents = (timelineData?.events || []).filter((e) => {
    if (selectedType !== 'all' && e.event_type !== selectedType) {
      return false;
    }
    if (onlyContradictions && !e.contradiction_flag) {
      return false;
    }
    return true;
  });

  return (
    <div className="rounded-3xl bg-white border border-slate-200 p-6 flex flex-col h-full overflow-hidden shadow-xs text-slate-900">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 shrink-0">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-teal-50 text-teal-700 border border-teal-200">
              <Clock className="w-4 h-4" />
            </div>
            <h2 className="text-sm font-bold text-slate-900">Medical History Timeline</h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-teal-50 text-teal-800 border border-teal-200">
              Chronological View
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Patient: <span className="text-teal-800 font-semibold">{patientName}</span> •
            Chronological clinical events with separate event and document dates
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleExtractTimeline}
            disabled={isExtracting}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold border border-slate-200 transition-colors cursor-pointer disabled:opacity-50"
          >
            {isExtracting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-700" />
            ) : (
              <RefreshCw className="w-3.5 h-3.5 text-teal-700" />
            )}
            <span>Update Timeline Events</span>
          </button>
        </div>
      </div>

      {/* Conflicting Information Alert Card */}
      {timelineData && timelineData.contradictions.length > 0 && (
        <div className="mt-4 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 space-y-3 shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
              <h3 className="text-xs font-bold text-amber-900">
                Conflicting Information Detected ({timelineData.contradictions.length})
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                Review Required
              </span>
            </div>
            <button
              type="button"
              onClick={() => setExpandedContradictions(!expandedContradictions)}
              className="p-1 rounded text-amber-800 hover:text-amber-950 transition-colors"
            >
              {expandedContradictions ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>

          {expandedContradictions && (
            <div className="space-y-2.5 max-h-48 overflow-y-auto pr-1">
              {timelineData.contradictions.map((c, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-white border border-amber-200 space-y-1.5"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-amber-900 capitalize">
                      {c.conflict_type.replace('_', ' ')}
                    </span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                        c.severity === 'critical'
                          ? 'bg-rose-100 text-rose-800 border border-rose-300'
                          : 'bg-amber-100 text-amber-800 border border-amber-300'
                      }`}
                    >
                      {c.severity}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-700 leading-relaxed">{c.explanation}</p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px] pt-1">
                    <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-slate-500 block truncate">
                        Source 1: {c.document_title_1} (Page {c.page_number_1 || 1})
                      </span>
                      <span className="text-slate-900 font-medium mt-0.5 block truncate">
                        {c.event_1_summary}
                      </span>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-slate-500 block truncate">
                        Source 2: {c.document_title_2} (Page {c.page_number_2 || 1})
                      </span>
                      <span className="text-slate-900 font-medium mt-0.5 block truncate">
                        {c.event_2_summary}
                      </span>
                    </div>
                  </div>

                  {c.suggested_resolution && (
                    <div className="text-[10px] text-teal-800 pt-1 flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3 text-teal-700 shrink-0" />
                      <span>Suggested Guidance: {c.suggested_resolution}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Filter and Metrics Toolbar */}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100 shrink-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            type="button"
            onClick={() => setSelectedType('all')}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
              selectedType === 'all'
                ? 'bg-teal-700 text-white'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
            }`}
          >
            All Events ({timelineData?.summary.total_events || 0})
          </button>

          {(['diagnosis', 'medication', 'procedure', 'lab_result', 'allergy', 'encounter'] as ClinicalEventType[]).map(
            (type) => {
              const count = timelineData?.summary.event_counts_by_type[type] || 0;
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => setSelectedType(type)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors flex items-center space-x-1 cursor-pointer ${
                    selectedType === type
                      ? 'bg-teal-700 text-white font-semibold'
                      : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  }`}
                >
                  {getEventIcon(type)}
                  <span className="capitalize">{type.replace('_', ' ')}</span>
                  <span className="text-[10px] opacity-75">({count})</span>
                </button>
              );
            }
          )}
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <label className="flex items-center space-x-1.5 cursor-pointer text-slate-700">
            <input
              type="checkbox"
              checked={onlyContradictions}
              onChange={(e) => setOnlyContradictions(e.target.checked)}
              className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
            />
            <span className="text-[11px] text-amber-800 font-semibold">Conflicts Only</span>
          </label>

          <button
            type="button"
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer text-[11px]"
          >
            <span>Order:</span>
            <span className="font-semibold text-teal-800">
              {sortOrder === 'asc' ? 'Oldest First' : 'Newest First'}
            </span>
          </button>
        </div>
      </div>

      {/* Main Timeline Stream */}
      <div className="mt-4 flex-1 overflow-y-auto space-y-4 pr-1">
        {isLoading ? (
          <div className="py-20 text-center text-xs text-slate-500 flex flex-col items-center justify-center space-y-2">
            <Loader2 className="w-5 h-5 animate-spin text-teal-700" />
            <span>Assembling chronological patient history...</span>
          </div>
        ) : error ? (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="py-20 text-center text-slate-500 flex flex-col items-center justify-center space-y-2">
            <Clock className="w-10 h-10 text-slate-300" />
            <p className="text-xs font-semibold text-slate-700">No events found for this filter</p>
            <p className="text-[11px] text-slate-500">
              Upload documents or click &quot;Update Timeline Events&quot; to populate events.
            </p>
          </div>
        ) : (
          <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
            {filteredEvents.map((ev) => (
              <div
                key={ev.id}
                className={`relative p-4 rounded-2xl border transition-all ${
                  ev.contradiction_flag
                    ? 'bg-amber-50/70 border-amber-300'
                    : 'bg-slate-50 border-slate-200 hover:border-slate-300 hover:bg-white'
                }`}
              >
                {/* Timeline Node Marker */}
                <div
                  className={`absolute -left-[27px] top-4.5 w-3 h-3 rounded-full border-2 border-white ${
                    ev.contradiction_flag ? 'bg-amber-500 animate-pulse' : 'bg-teal-700'
                  }`}
                />

                {/* Event Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-200">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-0.5 rounded-lg border text-xs font-semibold flex items-center space-x-1 ${getEventBadgeClass(
                        ev.event_type
                      )}`}
                    >
                      {getEventIcon(ev.event_type)}
                      <span className="capitalize">{ev.event_type.replace('_', ' ')}</span>
                    </span>

                    <span className="px-2 py-0.5 rounded-lg bg-white border border-slate-200 text-[11px] font-semibold text-slate-800">
                      {ev.event_date}
                    </span>

                    {getPrecisionBadge(ev.event_date_precision)}

                    {ev.document_date && ev.document_date !== ev.event_date && (
                      <span className="text-[10px] text-slate-500">
                        (Document Date: {ev.document_date})
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase ${
                        ev.clinical_status === 'active'
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                          : ev.clinical_status === 'resolved'
                          ? 'bg-blue-50 text-blue-800 border border-blue-200'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {ev.clinical_status}
                    </span>

                    {ev.contradiction_flag && (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 flex items-center space-x-1">
                        <AlertOctagon className="w-3 h-3 text-amber-700" />
                        <span>Conflicting</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Event Body */}
                <div className="mt-2.5 space-y-1.5">
                  <div className="text-xs font-bold text-slate-900">{ev.description}</div>

                  {ev.value_or_dosage && (
                    <div className="text-xs font-medium text-teal-800 bg-teal-50 px-2.5 py-1 rounded-lg border border-teal-200 inline-block">
                      {ev.value_or_dosage}
                    </div>
                  )}

                  {ev.contradiction_details && (
                    <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-[11px] text-amber-900 leading-relaxed">
                      <span className="font-bold block mb-0.5">Conflicting Evidence Details:</span>
                      {ev.contradiction_details}
                    </div>
                  )}
                </div>

                {/* Event Source Provenance Footer */}
                <div className="mt-3 pt-2 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
                  <div className="flex items-center space-x-2 truncate">
                    <FileText className="w-3.5 h-3.5 text-teal-700 shrink-0" />
                    <span className="truncate">{ev.document_title || 'Document Record'}</span>
                    <span>•</span>
                    <span>Page {ev.page_number || 1}</span>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleOpenCitation(ev)}
                    className="flex items-center space-x-1 text-teal-700 hover:text-teal-800 transition-colors font-semibold cursor-pointer shrink-0 ml-2"
                  >
                    <span>View Supporting Source</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* PDF Citation Provenance Modal */}
      <PDFCitationViewerModal
        isOpen={isCitationModalOpen}
        onClose={() => setIsCitationModalOpen(false)}
        citation={citationForModal}
      />
    </div>
  );
};
