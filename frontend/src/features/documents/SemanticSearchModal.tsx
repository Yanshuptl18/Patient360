import React, { useState, useEffect } from 'react';
import {
  X,
  Search,
  AlertCircle,
  FileText,
} from 'lucide-react';
import { VectorSearchResultItem, VectorStatsResponse } from '../../types';
import { useAuth } from '../auth/AuthContext';

interface SemanticSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientId: string;
  patientName: string;
}

const PRESET_QUERIES = [
  'EGFR mutation exon 21 alteration',
  'Clinical impression and diagnosis',
  'Prescribed medications and dosages',
  'Documented allergies and adverse reactions',
  'Pathology and biopsy findings',
];

export const SemanticSearchModal: React.FC<SemanticSearchModalProps> = ({
  isOpen,
  onClose,
  patientId,
  patientName,
}) => {
  const { token } = useAuth();
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [results, setResults] = useState<VectorSearchResultItem[]>([]);
  const [stats, setStats] = useState<VectorStatsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    if (!isOpen || !token) return;

    const fetchStats = async () => {
      try {
        const response = await fetch('/api/v1/vector/stats', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (response.ok) {
          const data: VectorStatsResponse = await response.json();
          setStats(data);
        }
      } catch (err) {
        console.warn('Unable to load collection statistics:', err);
      }
    };

    fetchStats();
  }, [isOpen, token]);

  if (!isOpen) return null;

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await fetch('/api/v1/vector/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: query.trim(),
          patient_id: patientId,
          top_k: topK,
          score_threshold: 0.0,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'We could not complete your search.');
      }

      const data: VectorSearchResultItem[] = await response.json();
      setResults(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An error occurred during medical evidence search.');
      }
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 0.8) return 'bg-teal-50 text-teal-800 border-teal-200';
    if (score >= 0.7) return 'bg-blue-50 text-blue-800 border-blue-200';
    if (score >= 0.6) return 'bg-amber-50 text-amber-800 border-amber-200';
    return 'bg-slate-100 text-slate-700 border-slate-200';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] rounded-3xl bg-white border border-slate-200 shadow-xl p-6 flex flex-col overflow-hidden text-slate-900">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-2xl bg-teal-50 text-teal-700 border border-teal-200">
              <Search className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-slate-900">Search Medical Evidence</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-teal-50 text-teal-800 border border-teal-200">
                  Patient Scoped {stats ? `• ${stats.vectors_count} passages` : ''}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Restricted to authorized patient dossier:{' '}
                <span className="text-teal-800 font-semibold">{patientName}</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Input Bar */}
        <form onSubmit={handleSearch} className="mt-4 flex flex-col gap-2 shrink-0">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter clinical symptoms, molecular markers, diagnoses, or medications..."
                className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-xs placeholder-slate-400 focus:outline-none focus:border-teal-600 focus:bg-white transition-colors"
              />
            </div>

            <div className="flex items-center space-x-1.5 px-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600">
              <span>Results:</span>
              <select
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                className="bg-transparent text-slate-900 font-medium focus:outline-none"
              >
                <option value="3">3</option>
                <option value="5">5</option>
                <option value="10">10</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-4 py-2 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs shadow-xs disabled:opacity-50 flex items-center space-x-2 transition-all cursor-pointer"
            >
              {isLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-3.5 h-3.5" />
                  <span>Search</span>
                </>
              )}
            </button>
          </div>

          {/* Quick Query Suggestions */}
          <div className="flex items-center gap-1.5 flex-wrap pt-1">
            <span className="text-[11px] text-slate-500 font-medium">Suggested queries:</span>
            {PRESET_QUERIES.map((preset) => (
              <button
                key={preset}
                type="button"
                onClick={() => setQuery(preset)}
                className="px-2 py-0.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] transition-colors border border-slate-200 cursor-pointer"
              >
                {preset}
              </button>
            ))}
          </div>
        </form>

        {/* Results Container */}
        <div className="mt-4 flex-1 overflow-y-auto space-y-3 pr-1">
          {error && (
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 flex items-center space-x-3 text-rose-800 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          {!hasSearched && !isLoading && (
            <div className="py-16 text-center text-slate-500 flex flex-col items-center justify-center space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400">
                <Search className="w-6 h-6" />
              </div>
              <p className="text-xs font-semibold text-slate-700">Enter a query to find relevant evidence</p>
              <p className="text-[11px] text-slate-500 max-w-sm">
                Searches across all attached clinical notes, discharge summaries, and lab panels.
              </p>
            </div>
          )}

          {hasSearched && !isLoading && results.length === 0 && !error && (
            <div className="py-16 text-center text-slate-500 flex flex-col items-center justify-center space-y-2">
              <AlertCircle className="w-8 h-8 text-slate-400" />
              <p className="text-xs font-semibold text-slate-700">No matching medical records found</p>
              <p className="text-[11px] text-slate-500 max-w-sm">
                Try alternative clinical keywords or broaden your search criteria.
              </p>
            </div>
          )}

          {results.map((item, idx) => (
            <div
              key={`${item.chunk_id}-${idx}`}
              className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2.5 hover:border-slate-300 transition-colors"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                <div className="flex items-center space-x-2">
                  <FileText className="w-3.5 h-3.5 text-teal-700" />
                  <span className="font-semibold text-slate-900">{item.doc_title}</span>
                  <span className="text-slate-400">•</span>
                  <span className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[10px] font-medium text-slate-700">
                    Page {item.page_number}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${getScoreBadgeColor(
                      item.score
                    )}`}
                  >
                    Match: {Math.round(item.score * 100)}%
                  </span>
                </div>
              </div>

              <div className="text-xs text-slate-700 leading-relaxed font-sans bg-white p-3 rounded-xl border border-slate-200">
                {item.content}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
