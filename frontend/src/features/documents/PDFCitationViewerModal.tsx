import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  Quote,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Download,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Layers,
  Search,
} from 'lucide-react';
import { CitationItem, DocumentChunk } from '../../types';
import { useAuth } from '../auth/AuthContext';

interface PDFCitationViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  citation: CitationItem | null;
}

export const PDFCitationViewerModal: React.FC<PDFCitationViewerModalProps> = ({
  isOpen,
  onClose,
  citation,
}) => {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState<'excerpt' | 'pdf'>('excerpt');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageChunks, setPageChunks] = useState<DocumentChunk[]>([]);
  const [allChunks, setAllChunks] = useState<DocumentChunk[]>([]);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [isLoadingPdf, setIsLoadingPdf] = useState(false);
  const [isLoadingChunks, setIsLoadingChunks] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync state when citation opens
  useEffect(() => {
    if (!isOpen || !citation) {
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl);
        setPdfBlobUrl(null);
      }
      return;
    }

    setCurrentPage(citation.page_number || 1);
    setActiveTab('excerpt');
    setError(null);

    // Fetch chunks for document to display page text & context
    const loadDocumentChunks = async () => {
      if (!token) return;
      setIsLoadingChunks(true);
      try {
        const res = await fetch(`/api/v1/documents/${citation.document_id}/chunks`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const chunks: DocumentChunk[] = await res.json();
          setAllChunks(chunks);
          const maxPage = Math.max(1, ...chunks.map((c) => c.page_number));
          setTotalPages(maxPage);
        }
      } catch (err) {
        console.warn('Could not load chunks for citation document:', err);
      } finally {
        setIsLoadingChunks(false);
      }
    };

    loadDocumentChunks();
  }, [isOpen, citation, token]);

  // Load PDF Blob when PDF tab is selected
  useEffect(() => {
    if (!isOpen || !citation || activeTab !== 'pdf' || pdfBlobUrl || !token) return;

    const loadPdfBlob = async () => {
      setIsLoadingPdf(true);
      setError(null);
      try {
        const res = await fetch(`/api/v1/documents/${citation.document_id}/download`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          throw new Error('Unable to stream PDF binary from repository.');
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        setPdfBlobUrl(url);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Failed to stream PDF binary.');
        }
      } finally {
        setIsLoadingPdf(false);
      }
    };

    loadPdfBlob();
  }, [isOpen, citation, activeTab, pdfBlobUrl, token]);

  // Update visible chunks when currentPage changes
  useEffect(() => {
    if (allChunks.length > 0) {
      const filtered = allChunks.filter((c) => c.page_number === currentPage);
      setPageChunks(filtered);
    }
  }, [currentPage, allChunks]);

  if (!isOpen || !citation) return null;

  const handleCopyQuote = () => {
    if (!citation.exact_quote) return;
    navigator.clipboard.writeText(citation.exact_quote);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const getStatusBadge = () => {
    switch (citation.verification_status) {
      case 'supported':
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Supported Provenance</span>
          </span>
        );
      case 'partially_supported':
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30 flex items-center space-x-1">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
            <span>Partially Supported</span>
          </span>
        );
      case 'unsupported':
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30 flex items-center space-x-1">
            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            <span>Unsupported Claim</span>
          </span>
        );
    }
  };

  // Helper to render text with quote highlighting
  const renderHighlightedContent = (rawText: string, quote: string) => {
    if (!quote || !rawText) return rawText;

    const normalizedRaw = rawText.toLowerCase();
    const normalizedQuote = quote.toLowerCase();
    const matchIndex = normalizedRaw.indexOf(normalizedQuote);

    if (matchIndex === -1) {
      return rawText;
    }

    const before = rawText.slice(0, matchIndex);
    const matched = rawText.slice(matchIndex, matchIndex + quote.length);
    const after = rawText.slice(matchIndex + quote.length);

    return (
      <>
        {before}
        <mark className="bg-amber-400/25 text-amber-200 border-b-2 border-amber-400 px-1 py-0.5 rounded shadow-sm shadow-amber-400/10 font-medium">
          {matched}
        </mark>
        {after}
      </>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-5xl h-[88vh] rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl p-6 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 shrink-0">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="p-2.5 rounded-2xl bg-teal-500/10 text-teal-400 border border-teal-500/20 shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="overflow-hidden">
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-semibold text-white truncate max-w-lg">
                  {citation.document_title}
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-[10px] font-mono shrink-0">
                  Page {citation.page_number}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 truncate">
                Doc ID: <span className="font-mono text-slate-300">{citation.document_id}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            {getStatusBadge()}
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors ml-2 cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Claim & Exact Quote Banner */}
        <div className="my-3 p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2 shrink-0">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-slate-400">
              <Quote className="w-3.5 h-3.5 text-teal-400" />
              <span className="font-semibold text-slate-200">Synthesized Claim:</span>
              <span className="text-slate-300 italic truncate max-w-md">
                &quot;{citation.claim_text}&quot;
              </span>
            </div>
            <button
              type="button"
              onClick={handleCopyQuote}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-teal-300 text-xs transition-colors cursor-pointer"
            >
              {isCopied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400 font-medium">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Exact Quote</span>
                </>
              )}
            </button>
          </div>

          <div className="p-2.5 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-200 text-xs font-mono leading-relaxed">
            &quot;{citation.exact_quote}&quot;
          </div>
        </div>

        {/* View Switcher & Page Navigation Toolbar */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 shrink-0">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => setActiveTab('excerpt')}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                activeTab === 'excerpt'
                  ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center space-x-1.5">
                <Search className="w-3.5 h-3.5" />
                <span>Page Excerpt & Provenance</span>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('pdf')}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                activeTab === 'pdf'
                  ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center space-x-1.5">
                <FileText className="w-3.5 h-3.5" />
                <span>Original PDF Stream</span>
              </div>
            </button>
          </div>

          {/* Page Jumper */}
          <div className="flex items-center space-x-2">
            <button
              type="button"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 transition-colors cursor-pointer"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>

            <span className="text-xs text-slate-300 font-mono">
              Page <span className="font-semibold text-teal-400">{currentPage}</span> of{' '}
              {totalPages}
            </span>

            <button
              type="button"
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 transition-colors cursor-pointer"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-hidden mt-3 relative">
          {error && (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {activeTab === 'excerpt' ? (
            <div className="h-full overflow-y-auto space-y-3 pr-1">
              {isLoadingChunks ? (
                <div className="py-20 text-center text-xs text-slate-400">
                  Retrieving page extraction and provenance anchors...
                </div>
              ) : pageChunks.length > 0 ? (
                pageChunks.map((chunk) => (
                  <div
                    key={chunk.id}
                    className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 space-y-2 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded-md bg-teal-500/10 text-teal-400 border border-teal-500/20 font-mono text-[10px]">
                          Chunk #{chunk.chunk_index + 1}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono">
                          Page {chunk.page_number} • {chunk.token_count} tokens
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        ID: {chunk.id.slice(0, 8)}...
                      </span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/60 text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-wrap">
                      {renderHighlightedContent(chunk.raw_content, citation.exact_quote)}
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-16 text-center text-slate-400 space-y-2">
                  <Layers className="w-8 h-8 mx-auto text-slate-600" />
                  <p className="text-xs">No extracted chunks found for Page {currentPage}.</p>
                  <p className="text-[11px] text-slate-500">
                    Switch to original PDF stream or select another page.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full w-full rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden flex flex-col">
              {isLoadingPdf ? (
                <div className="py-24 text-center text-xs text-slate-400">
                  Streaming binary PDF from secure repository...
                </div>
              ) : pdfBlobUrl ? (
                <iframe
                  title="PDF Document Citation Stream"
                  src={`${pdfBlobUrl}#page=${currentPage}`}
                  className="w-full h-full rounded-2xl border-0"
                />
              ) : (
                <div className="py-24 text-center text-xs text-slate-400 space-y-3">
                  <FileText className="w-8 h-8 mx-auto text-slate-600" />
                  <p>PDF Stream unavailable.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer info & External open */}
        <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 shrink-0">
          <div className="flex items-center space-x-2">
            <span>Evidence provenance grounded to Page {citation.page_number}</span>
            <span>•</span>
            <span className="text-teal-400/80">Phase 8 Advanced Hybrid RAG</span>
          </div>

          <div className="flex items-center space-x-3">
            <a
              href={`/api/v1/documents/${citation.document_id}/download`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1 text-slate-400 hover:text-teal-300 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Raw PDF</span>
            </a>
            {pdfBlobUrl && (
              <a
                href={pdfBlobUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center space-x-1 text-teal-400 hover:text-teal-300 transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Open in Native Tab</span>
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
