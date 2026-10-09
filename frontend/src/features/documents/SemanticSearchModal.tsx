import React, { useState, useEffect } from 'react';
import {
  X,
  Search,
  Sparkles,
  Database,
  ShieldCheck,
  Calendar,
  AlertCircle,
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
  'EGFR L858R mutation exon 21',
  'Clinical impression and diagnosis',
  'Targeted tyrosine kinase inhibitor therapy',
  'Severe persistent cough and dyspnea',
  'Pathology biopsy report findings',
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

  // Fetch vector collection health/statistics on open
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
        console.warn('Unable to load vector collection stats:', err);
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
        throw new Error(errorData.detail || 'Vector semantic search failed.');
      }

      const data: VectorSearchResultItem[] = await response.json();
      setResults(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred during semantic search.');
      }
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 0.8) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
    if (score >= 0.7) return 'bg-teal-500/15 text-teal-400 border-teal-500/30';
    if (score >= 0.6) return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
    return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl p-6 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-2xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-semibold text-white">Dense Vector Semantic Search</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-teal-500/10 text-teal-400 border border-teal-500/20">
                  FastEmbed 384-d
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  Cosine HNSW
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Isolated clinical retrieval scoped strictly to patient dossier:{' '}
                <span className="text-teal-400 font-medium">{patientName}</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Collection Status Bar */}
        {stats && (
          <div className="mt-3 px-3 py-2 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400 shrink-0">
            <div className="flex items-center space-x-2">
              <Database className="w-3.5 h-3.5 text-teal-400" />
              <span>
                Collection:{' '}
                <span className="text-slate-200 font-mono text-[11px]">{stats.collection_name}</span>
              </span>
              <span className="text-slate-600">•</span>
              <span>
                Total Vectors: <span className="text-teal-400 font-medium">{stats.vectors_count}</span>
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">
                {stats.is_embedded ? 'Embedded In-Memory Qdrant' : 'Active Qdrant Daemon'}
              </span>
            </div>
          </div>
        )}

        {/* Search Input Bar */}
        <form onSubmit={handleSearch} className="mt-4 flex flex-col gap-2 shrink-0">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5 pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter clinical symptoms, molecular mutations, diagnoses, or medications..."
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-sm placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
              />
            </div>

            <div className="flex items-center space-x-1.5 px-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400">
              <span>Top-K:</span>
              <select
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                className="bg-transparent text-slate-200 font-medium focus:outline-none"
              >
                <option value="3" className="bg-slate-900">3</option>
                <option value="5" className="bg-slate-900">5</option>
                <option value="10" className="bg-slate-900">10</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-semibold text-sm shadow-lg shadow-teal-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-all cursor-pointer"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Search</span>
                </>
              )}
            </button>
          </div>

          {/* Quick Query Suggestions */}
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

        {/* Results Container */}
        <div className="mt-4 flex-1 overflow-y-auto space-y-3 pr-1">
          {error && (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center space-x-3 text-rose-400 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!hasSearched && !isLoading && (
            <div className="py-16 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-slate-800/40 border border-slate-800 flex items-center justify-center text-slate-400">
                <Search className="w-6 h-6" />
              </div>
              <div className="max-w-md">
                <h3 className="text-sm font-medium text-slate-300 mb-1">Vector Search Ready</h3>
                <p className="text-xs text-slate-500">
                  Enter a clinical query or select one of the suggested keywords above to perform dense
                  retrieval against patient chunks indexed in Qdrant.
                </p>
              </div>
            </div>
          )}

          {hasSearched && !isLoading && results.length === 0 && !error && (
            <div className="py-16 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
              <AlertCircle className="w-8 h-8 text-slate-600" />
              <div>
                <h3 className="text-sm font-medium text-slate-300 mb-1">No Matching Chunks Found</h3>
                <p className="text-xs text-slate-500 max-w-sm">
                  No indexed chunks for this patient matched the semantic similarity query. Make sure
                  documents have been ingested and try alternative search terms.
                </p>
              </div>
            </div>
          )}

          {results.map((item, index) => (
            <div
              key={item.chunk_id}
              className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition-all space-y-2.5"
            >
              {/* Result Meta Bar */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center space-x-2">
                  <span className="w-6 h-6 rounded-lg bg-teal-500/10 text-teal-400 text-xs font-bold flex items-center justify-center border border-teal-500/20">
                    #{index + 1}
                  </span>
                  <span className="text-xs font-semibold text-white">{item.doc_title}</span>
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                    {item.doc_type}
                  </span>
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-teal-500/15 text-teal-300 border border-teal-500/30">
                    Page {item.page_number}
                  </span>
                  <span className="text-slate-500 text-xs">• Chunk {item.chunk_index}</span>
                </div>

                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-bold border ${getScoreBadgeColor(
                      item.score
                    )}`}
                  >
                    Cosine Score: {item.score.toFixed(4)} ({(item.score * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>

              {/* Chunk Content */}
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800/80 font-sans text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
                {item.content}
              </div>

              {/* Provenance Footer */}
              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-800/40">
                <div className="flex items-center space-x-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Verified Isolated Patient Scope: {patientName}</span>
                </div>
                {item.doc_date && (
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-3 h-3 text-slate-500" />
                    <span>Doc Date: {item.doc_date}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 shrink-0">
          <span>
            {hasSearched ? `Found ${results.length} ranked chunk matches` : 'Ready to retrieve'}
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
