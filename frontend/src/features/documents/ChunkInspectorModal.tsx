import React, { useState, useEffect } from 'react';
import { X, Layers, FileText, Hash, Calendar, AlertCircle } from 'lucide-react';
import { Document, DocumentChunk } from '../../types';
import { useAuth } from '../auth/AuthContext';

interface ChunkInspectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  document?: Document | null;
  documentId?: string;
  documentTitle?: string;
}

export const ChunkInspectorModal: React.FC<ChunkInspectorModalProps> = ({
  isOpen,
  onClose,
  document,
  documentId,
  documentTitle,
}) => {
  const { token } = useAuth();
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [selectedPage, setSelectedPage] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeDocId = document?.id || documentId;
  const activeTitle = document?.title || documentTitle || 'Clinical Document';

  useEffect(() => {
    if (!isOpen || !activeDocId || !token) return;

    const fetchChunks = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/v1/documents/${activeDocId}/chunks`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!response.ok) {
          throw new Error('Failed to load document content.');
        }
        const data: DocumentChunk[] = await response.json();
        setChunks(data);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('An unexpected error occurred loading document passages.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchChunks();
  }, [isOpen, activeDocId, token]);

  if (!isOpen || !activeDocId) return null;

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] rounded-3xl bg-white border border-slate-200 shadow-xl p-6 flex flex-col overflow-hidden text-slate-900">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-2xl bg-teal-50 text-teal-700 border border-teal-200">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-slate-900">Document Evidence Passages</h2>
                <span className="px-2 py-0.5 rounded-full bg-teal-50 text-teal-800 border border-teal-200 text-[10px] font-semibold">
                  Page-Anchored
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5 truncate max-w-lg">
                Document: <span className="text-slate-800 font-medium">{activeTitle}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Stats Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4 shrink-0">
          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="text-[11px] text-slate-500 flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-teal-700" />
              <span>Extracted Passages</span>
            </div>
            <div className="text-base font-bold text-slate-900 mt-1">{chunks.length}</div>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="text-[11px] text-slate-500 flex items-center space-x-1.5">
              <Hash className="w-3.5 h-3.5 text-blue-700" />
              <span>Word Length</span>
            </div>
            <div className="text-base font-bold text-slate-900 mt-1">{totalTokens.toLocaleString()} words</div>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="text-[11px] text-slate-500 flex items-center space-x-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-700" />
              <span>Physical Pages</span>
            </div>
            <div className="text-base font-bold text-slate-900 mt-1">{uniquePages.length}</div>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="text-[11px] text-slate-500 flex items-center space-x-1.5">
              <Calendar className="w-3.5 h-3.5 text-amber-700" />
              <span>Document Date</span>
            </div>
            <div className="text-base font-bold text-slate-900 mt-1">{document?.doc_date || 'Undated'}</div>
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 shrink-0">
          <div className="text-xs text-slate-500">
            Showing <span className="font-semibold text-slate-900">{filteredChunks.length}</span> passage
            {filteredChunks.length === 1 ? '' : 's'}
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-xs text-slate-600 font-medium">Filter Page:</label>
            <select
              value={selectedPage}
              onChange={(e) => setSelectedPage(e.target.value)}
              className="px-2.5 py-1 rounded-xl bg-white border border-slate-200 text-slate-800 text-xs focus:outline-none focus:border-teal-600"
            >
              <option value="all">All Pages ({uniquePages.length})</option>
              {uniquePages.map((pg) => (
                <option key={pg} value={pg.toString()}>
                  Page {pg}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto mt-4 space-y-3 pr-1">
          {isLoading ? (
            <div className="py-12 text-center text-xs text-slate-500">Loading document passages...</div>
          ) : error ? (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
          ) : filteredChunks.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500">No passages available.</div>
          ) : (
            filteredChunks.map((chunk) => (
              <div
                key={chunk.id}
                className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded-md bg-teal-50 text-teal-800 border border-teal-200 text-[10px] font-semibold">
                      Page {chunk.page_number}
                    </span>
                    <span className="text-[11px] text-slate-500">
                      Index #{chunk.chunk_index + 1}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    {chunk.token_count} words
                  </span>
                </div>
                <div className="text-xs text-slate-700 leading-relaxed font-sans bg-white p-3 rounded-xl border border-slate-200 whitespace-pre-wrap">
                  {chunk.content}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
