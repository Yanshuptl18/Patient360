import React, { useState } from 'react';
import {
  FileText,
  Upload,
  Download,
  Trash2,
  Clock,
  CheckCircle2,
  Filter,
  Eye,
  Loader2,
  Search,
  Check,
} from 'lucide-react';
import { Document, DocType } from '../../types';
import { useAuth } from '../auth/AuthContext';
import { DocumentUploadModal } from './DocumentUploadModal';
import { ChunkInspectorModal } from './ChunkInspectorModal';
import { SemanticSearchModal } from './SemanticSearchModal';

interface DocumentListProps {
  patientId: string;
  patientName: string;
  documents: Document[];
  onRefresh: () => void;
}

const DOC_TYPE_LABELS: Record<DocType, { label: string; color: string }> = {
  patient_record: { label: 'Patient Record', color: 'bg-teal-50 text-teal-800 border-teal-200' },
  lab_report: { label: 'Lab Report', color: 'bg-blue-50 text-blue-800 border-blue-200' },
  discharge_summary: { label: 'Discharge Summary', color: 'bg-amber-50 text-amber-800 border-amber-200' },
  research_paper: { label: 'Research Paper', color: 'bg-indigo-50 text-indigo-800 border-indigo-200' },
  clinical_guideline: { label: 'Clinical Guideline', color: 'bg-purple-50 text-purple-800 border-purple-200' },
};

export const DocumentList: React.FC<DocumentListProps> = ({
  patientId,
  patientName,
  documents,
  onRefresh,
}) => {
  const { token, user } = useAuth();
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [inspectingDocument, setInspectingDocument] = useState<Document | null>(null);
  const [isIngestingId, setIsIngestingId] = useState<string | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const handleIngest = async (doc: Document) => {
    setIsIngestingId(doc.id);
    try {
      const response = await fetch(`/api/v1/documents/${doc.id}/ingest`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        throw new Error('Document processing failed.');
      }
      onRefresh();
    } catch (err) {
      console.error('Processing error:', err);
    } finally {
      setIsIngestingId(null);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    if (filterType !== 'all' && doc.doc_type !== filterType) return false;
    return true;
  });

  const handleDownload = async (doc: Document) => {
    try {
      const response = await fetch(`/api/v1/documents/${doc.id}/download`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Download failed or unauthorized.');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = `${doc.title}.pdf`;
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download document:', err);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!window.confirm('Are you sure you want to remove this document from the record?')) {
      return;
    }
    setIsDeletingId(docId);
    try {
      const response = await fetch(`/api/v1/documents/${docId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        onRefresh();
      }
    } catch (err) {
      console.error('Failed to delete document:', err);
    } finally {
      setIsDeletingId(null);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="rounded-3xl bg-white border border-slate-200 p-6 flex flex-col h-full shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-teal-50 text-teal-700 border border-teal-200">
              <FileText className="w-4 h-4" />
            </div>
            <h2 className="text-sm font-bold text-slate-900">Attached Medical Documents</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Patient: <span className="text-teal-800 font-semibold">{patientName}</span> •{' '}
            {documents.length} document{documents.length === 1 ? '' : 's'} available
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Filter */}
          <div className="relative">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-xs focus:outline-none focus:border-teal-600 pr-8"
            >
              <option value="all">All Document Categories</option>
              <option value="patient_record">Patient Record / Clinical Note</option>
              <option value="lab_report">Laboratory Report</option>
              <option value="discharge_summary">Discharge Summary</option>
              <option value="research_paper">Research Paper</option>
              <option value="clinical_guideline">Clinical Guideline</option>
            </select>
            <Filter className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>

          {/* Search Button */}
          <button
            onClick={() => setIsSearchOpen(true)}
            className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-semibold transition-all flex items-center space-x-1.5 cursor-pointer"
          >
            <Search className="w-3.5 h-3.5 text-teal-700" />
            <span>Search Evidence</span>
          </button>

          {/* Upload Button */}
          {user?.role !== 'demo' && user?.role !== 'patient' && (
            <button
              onClick={() => setIsUploadOpen(true)}
              className="px-3.5 py-1.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold shadow-xs transition-all flex items-center space-x-1.5 cursor-pointer"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Add Document</span>
            </button>
          )}
        </div>
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto mt-4 space-y-3 pr-1">
        {filteredDocs.length === 0 ? (
          <div className="py-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center mx-auto mb-3 text-slate-400">
              <FileText className="w-6 h-6" />
            </div>
            <p className="text-xs font-medium text-slate-700">No medical documents found</p>
            <p className="text-[11px] text-slate-500 mt-1 max-w-sm mx-auto">
              Add clinical PDF summaries, discharge instructions, or laboratory reports to organize patient records.
            </p>
            {user?.role !== 'demo' && user?.role !== 'patient' && (
              <button
                onClick={() => setIsUploadOpen(true)}
                className="mt-4 px-3 py-1.5 rounded-xl bg-teal-50 hover:bg-teal-100 text-teal-800 text-xs font-medium transition-colors border border-teal-200 inline-flex items-center space-x-1.5 cursor-pointer"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Add First Document</span>
              </button>
            )}
          </div>
        ) : (
          filteredDocs.map((doc) => {
            const badge = DOC_TYPE_LABELS[doc.doc_type] || DOC_TYPE_LABELS.patient_record;
            return (
              <div
                key={doc.id}
                className="p-4 rounded-2xl bg-slate-50/70 border border-slate-200 hover:border-slate-300 hover:bg-white transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 group"
              >
                <div className="flex items-start space-x-3 min-w-0">
                  <div className="p-2.5 rounded-xl bg-white text-teal-700 border border-slate-200 shrink-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2">
                      <h4 className="text-xs font-bold text-slate-900 truncate max-w-sm">
                        {doc.title}
                      </h4>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${badge.color}`}
                      >
                        {badge.label}
                      </span>
                    </div>

                    <div className="flex items-center space-x-3 text-[11px] text-slate-500 mt-1">
                      <span>{formatFileSize(doc.file_size_bytes)}</span>
                      <span>•</span>
                      <span>Date: {doc.doc_date || 'Undated'}</span>
                      <span>•</span>
                      <span className="font-mono text-slate-400 text-[10px]">
                        ID: {doc.file_hash_sha256.substring(0, 8)}...
                      </span>
                    </div>

                    <div className="flex items-center space-x-3 text-[11px] text-slate-500 mt-1.5">
                      <span className="flex items-center space-x-1">
                        <span className="font-medium text-slate-700">v{doc.version}</span>
                        <span>record</span>
                      </span>
                      <span>•</span>
                      <span className="flex items-center space-x-1">
                        {doc.ingestion_status === 'completed' ? (
                          <span className="text-teal-700 font-medium flex items-center space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Examined and Ready</span>
                          </span>
                        ) : (
                          <span className="text-amber-700 font-medium flex items-center space-x-1">
                            <Clock className="w-3.5 h-3.5" />
                            <span>Processing Required</span>
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
                  {doc.ingestion_status !== 'completed' && user?.role !== 'demo' && user?.role !== 'patient' && (
                    <button
                      onClick={() => handleIngest(doc)}
                      disabled={isIngestingId === doc.id}
                      className="px-2.5 py-1.5 rounded-xl bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 text-xs font-medium flex items-center space-x-1 transition-all disabled:opacity-50 cursor-pointer"
                      title="Examine and Index Content"
                    >
                      {isIngestingId === doc.id ? (
                        <>
                          <Loader2 className="w-3 h-3 animate-spin" />
                          <span>Examining...</span>
                        </>
                      ) : (
                        <>
                          <Check className="w-3 h-3 text-teal-700" />
                          <span>Process</span>
                        </>
                      )}
                    </button>
                  )}

                  <button
                    onClick={() => setInspectingDocument(doc)}
                    className="p-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors cursor-pointer"
                    title="Inspect Extracted Evidence"
                  >
                    <Eye className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => handleDownload(doc)}
                    className="p-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors cursor-pointer"
                    title="Download Original PDF"
                  >
                    <Download className="w-4 h-4" />
                  </button>

                  {user?.role !== 'demo' && user?.role !== 'patient' && (
                    <button
                      onClick={() => handleDelete(doc.id)}
                      disabled={isDeletingId === doc.id}
                      className="p-1.5 rounded-xl bg-white hover:bg-rose-50 text-slate-400 hover:text-rose-600 border border-slate-200 transition-colors disabled:opacity-50 cursor-pointer"
                      title="Remove Document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Upload Modal */}
      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        patientId={patientId}
        patientName={patientName}
        onDocumentUploaded={() => onRefresh()}
      />

      {/* Chunk Inspector Modal */}
      {inspectingDocument && (
        <ChunkInspectorModal
          isOpen={!!inspectingDocument}
          onClose={() => setInspectingDocument(null)}
          documentId={inspectingDocument.id}
          documentTitle={inspectingDocument.title}
        />
      )}

      {/* Search Evidence Modal */}
      <SemanticSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        patientId={patientId}
        patientName={patientName}
      />
    </div>
  );
};
