import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  Quote,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  ChevronLeft,
  ChevronRight,
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
        console.warn('Could not load passages for citation document:', err);
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
          throw new Error('Unable to stream PDF from repository.');
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        setPdfBlobUrl(url);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Failed to display PDF document.');
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
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-50 text-teal-800 border border-teal-200 flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-700" />
            <span>Verified Supporting Evidence</span>
          </span>
        );
      case 'partially_supported':
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 flex items-center space-x-1">
            <AlertCircle className="w-3.5 h-3.5 text-amber-700" />
            <span>Partially Supported</span>
          </span>
        );
      case 'unsupported':
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200 flex items-center space-x-1">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>Insufficient Evidence</span>
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
        <mark className="bg-amber-100 text-amber-950 border-b-2 border-amber-500 px-1 py-0.5 rounded font-semibold">
          {matched}
        </mark>
        {after}
      </>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-5xl h-[88vh] rounded-3xl bg-white border border-slate-200 shadow-xl p-6 flex flex-col overflow-hidden text-slate-900">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 shrink-0">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="p-2.5 rounded-2xl bg-teal-50 text-teal-700 border border-teal-200 shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="overflow-hidden">
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-slate-900 truncate max-w-lg">
                  {citation.document_title}
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-teal-50 text-teal-800 border border-teal-200 text-[10px] font-semibold shrink-0">
                  Page {citation.page_number}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5 truncate">
                Document Reference: <span className="font-mono text-slate-700">{citation.document_id}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            {getStatusBadge()}
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors ml-2 cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Claim & Exact Quote Banner */}
        <div className="my-3 p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 shrink-0">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-slate-600">
              <Quote className="w-3.5 h-3.5 text-teal-700" />
              <span className="font-semibold text-slate-900">Clinical Statement:</span>
              <span className="text-slate-700 italic truncate max-w-md">
                &quot;{citation.claim_text}&quot;
              </span>
            </div>
            <button
              type="button"
              onClick={handleCopyQuote}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium transition-colors cursor-pointer"
            >
              {isCopied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-teal-700" />
                  <span className="text-teal-800 font-semibold">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Exact Quote</span>
                </>
              )}
            </button>
          </div>

          <div className="p-3 rounded-xl bg-teal-50/70 border border-teal-200 text-teal-900 text-xs font-serif leading-relaxed">
            &quot;{citation.exact_quote}&quot;
          </div>
        </div>

        {/* View Switcher & Page Navigation Toolbar */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 shrink-0">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => setActiveTab('excerpt')}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                activeTab === 'excerpt'
                  ? 'bg-teal-50 text-teal-800 border border-teal-200 font-bold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center space-x-1.5">
                <Search className="w-3.5 h-3.5" />
                <span>Extracted Page Evidence</span>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('pdf')}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                activeTab === 'pdf'
                  ? 'bg-teal-50 text-teal-800 border border-teal-200 font-bold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center space-x-1.5">
                <FileText className="w-3.5 h-3.5" />
                <span>Original PDF Document</span>
              </div>
            </button>
          </div>

          {/* Page Jumper */}
          <div className="flex items-center space-x-2">
            <button
              type="button"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed text-slate-700 transition-colors cursor-pointer"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>

            <span className="text-xs text-slate-700 font-medium">
              Page <span className="font-bold text-teal-800">{currentPage}</span> of{' '}
              {totalPages}
            </span>

            <button
              type="button"
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed text-slate-700 transition-colors cursor-pointer"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-hidden mt-3 relative">
          {error && (
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {activeTab === 'excerpt' ? (
            <div className="h-full overflow-y-auto space-y-3 pr-1">
              {isLoadingChunks ? (
                <div className="py-20 text-center text-xs text-slate-500">
                  Retrieving page extraction and supporting evidence...
                </div>
              ) : pageChunks.length > 0 ? (
                pageChunks.map((chunk) => (
                  <div
                    key={chunk.id}
                    className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 hover:border-slate-300 transition-colors"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded-md bg-teal-50 text-teal-800 border border-teal-200 text-[10px] font-semibold">
                          Section #{chunk.chunk_index + 1}
                        </span>
                        <span className="text-[11px] text-slate-500">
                          Page {chunk.page_number} • {chunk.token_count} words
                        </span>
                      </div>
                    </div>

                    <div className="p-3.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 leading-relaxed font-sans whitespace-pre-wrap">
                      {renderHighlightedContent(chunk.raw_content, citation.exact_quote)}
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-20 text-center text-xs text-slate-500">
                  No extracted passages found for page {currentPage}.
                </div>
              )}
            </div>
          ) : (
            <div className="h-full w-full rounded-2xl overflow-hidden border border-slate-200 bg-slate-50 relative flex items-center justify-center">
              {isLoadingPdf ? (
                <div className="text-xs text-slate-500">Loading original PDF stream...</div>
              ) : pdfBlobUrl ? (
                <iframe
                  src={`${pdfBlobUrl}#page=${currentPage}`}
                  className="w-full h-full border-0"
                  title="Original PDF Document"
                />
              ) : (
                <div className="text-xs text-slate-500">No PDF stream available.</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
