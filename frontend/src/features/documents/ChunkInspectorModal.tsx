import React, { useState, useEffect } from 'react';
import { X, Layers, FileText, Hash, Calendar, AlertCircle } from 'lucide-react';
import { Document, DocumentChunk } from '../../types';
import { useAuth } from '../auth/AuthContext';

interface ChunkInspectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document | null;
}

export const ChunkInspectorModal: React.FC<ChunkInspectorModalProps> = ({
  isOpen,
  onClose,
  document,
}) => {
  const { token } = useAuth();
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [selectedPage, setSelectedPage] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !document || !token) return;

    const fetchChunks = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/v1/documents/${document.id}/chunks`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!response.ok) {
          throw new Error('Failed to load document chunks.');
        }
        const data: DocumentChunk[] = await response.json();
        setChunks(data);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('An unexpected error occurred loading chunks.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchChunks();
  }, [isOpen, document, token]);

  if (!isOpen || !document) return null;

  // Derive unique page numbers
  const uniquePages = Array.from(new Set(chunks.map((c) => c.page_number))).sort(
    (a, b) => a - b
  );
  const totalTokens = chunks.reduce((acc, c) => acc + c.token_count, 0);

  const filteredChunks = chunks.filter((c) => {
    if (selectedPage !== 'all' && c.page_number !== parseInt(selectedPage, 10)) {
      return false;
    }
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl p-6 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-2xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-semibold text-white">Semantic Chunks & Provenance Inspector</h2>
                <span className="px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20 text-[10px] font-mono">
                  Phase 5
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 truncate max-w-lg">
                Document: <span className="text-slate-200 font-medium">{document.title}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Stats Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4 shrink-0">
          <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800">
            <div className="text-[11px] text-slate-400 flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-teal-400" />
              <span>Extracted Chunks</span>
            </div>
            <div className="text-base font-bold text-white mt-1">{chunks.length}</div>
          </div>

          <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800">
            <div className="text-[11px] text-slate-400 flex items-center space-x-1.5">
              <Hash className="w-3.5 h-3.5 text-cyan-400" />
              <span>Total Tokens</span>
            </div>
            <div className="text-base font-bold text-white mt-1">{totalTokens.toLocaleString()}</div>
          </div>

          <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800">
            <div className="text-[11px] text-slate-400 flex items-center space-x-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span>Physical Pages</span>
            </div>
            <div className="text-base font-bold text-white mt-1">{uniquePages.length}</div>
          </div>

          <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800">
            <div className="text-[11px] text-slate-400 flex items-center space-x-1.5">
              <Calendar className="w-3.5 h-3.5 text-amber-400" />
              <span>Document Date</span>
            </div>
            <div className="text-base font-bold text-white mt-1">{document.doc_date || 'Undated'}</div>
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 shrink-0">
          <div className="text-xs text-slate-400">
            Showing <span className="font-semibold text-slate-200">{filteredChunks.length}</span> chunk
            {filteredChunks.length === 1 ? '' : 's'}
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-xs text-slate-400">Page Filter:</label>
            <select
              value={selectedPage}
              onChange={(e) => setSelectedPage(e.target.value)}
              className="px-2.5 py-1 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-teal-500"
            >
              <option value="all">All Pages ({chunks.length})</option>
              {uniquePages.map((pg) => (
                <option key={pg} value={pg.toString()}>
                  Page {pg}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Chunks Scrollable View */}
        <div className="flex-1 overflow-y-auto mt-4 space-y-4 pr-1">
          {isLoading ? (
            <div className="py-16 text-center text-xs text-slate-400">
              Loading extracted chunks with page provenance...
            </div>
          ) : error ? (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          ) : filteredChunks.length === 0 ? (
            <div className="py-16 text-center">
              <Layers className="w-10 h-10 text-slate-600 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-300">No chunks available</p>
              <p className="text-[11px] text-slate-500 mt-1">
                Trigger ingestion on this document to extract and chunk text.
              </p>
            </div>
          ) : (
            filteredChunks.map((chunk) => (
              <div
                key={chunk.id}
                className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-all space-y-3"
              >
                {/* Chunk Meta Header */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded-lg bg-teal-500/10 text-teal-400 border border-teal-500/20 text-xs font-semibold">
                      Chunk #{chunk.chunk_index + 1}
                    </span>
                    <span className="px-2 py-0.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-semibold">
                      Page {chunk.page_number}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3 text-[11px] text-slate-400 font-mono">
                    <span>{chunk.token_count} tokens</span>
                    <span>•</span>
                    <span className="text-slate-500 text-[10px]">ID: {chunk.id.substring(0, 8)}...</span>
                  </div>
                </div>

                {/* Injected Context Header */}
                <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-[11px] font-mono text-teal-300/90">
                  {chunk.content.split('\n')[0]}
                </div>

                {/* Raw Passage Text */}
                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800/60 text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-wrap">
                  {chunk.raw_content}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
