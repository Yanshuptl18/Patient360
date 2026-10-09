import React, { useState } from 'react';
import {
  FileText,
  Upload,
  Download,
  Trash2,
  Clock,
  CheckCircle2,
  AlertCircle,
  Filter,
} from 'lucide-react';
import { Document, DocType } from '../../types';
import { useAuth } from '../auth/AuthContext';
import { DocumentUploadModal } from './DocumentUploadModal';

interface DocumentListProps {
  patientId: string;
  patientName: string;
  documents: Document[];
  onRefresh: () => void;
}

const DOC_TYPE_LABELS: Record<DocType, { label: string; color: string }> = {
  patient_record: { label: 'Patient Record', color: 'bg-teal-500/10 text-teal-400 border-teal-500/20' },
  lab_report: { label: 'Lab Report', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
  discharge_summary: { label: 'Discharge Summary', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  research_paper: { label: 'Research Paper', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
  clinical_guideline: { label: 'Guideline', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
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
    if (!window.confirm('Are you sure you want to delete this document from the dossier?')) {
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
    <div className="rounded-3xl bg-slate-900/60 border border-slate-800 p-6 flex flex-col h-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-teal-500/10 text-teal-400">
              <FileText className="w-4 h-4" />
            </div>
            <h2 className="text-sm font-semibold text-white">Attached Clinical Documents</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Patient Dossier: <span className="text-teal-400 font-medium">{patientName}</span> •{' '}
            {documents.length} document{documents.length === 1 ? '' : 's'} registered
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Filter */}
          <div className="relative">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-xs focus:outline-none focus:border-teal-500 pr-8"
            >
              <option value="all">All Document Types</option>
              <option value="patient_record">Patient Record / EHR</option>
              <option value="lab_report">Lab Report</option>
              <option value="discharge_summary">Discharge Summary</option>
              <option value="research_paper">Research Paper</option>
              <option value="clinical_guideline">Clinical Guideline</option>
            </select>
            <Filter className="w-3.5 h-3.5 text-slate-500 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>

          {/* Upload Button */}
          {user?.role !== 'demo' && (
            <button
              onClick={() => setIsUploadOpen(true)}
              className="px-3 py-1.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-semibold shadow-lg shadow-teal-500/20 transition-all flex items-center space-x-1.5"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Upload PDF</span>
            </button>
          )}
        </div>
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto mt-4 space-y-3 pr-1">
        {filteredDocs.length === 0 ? (
          <div className="py-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-center mx-auto mb-3 text-slate-500">
              <FileText className="w-6 h-6" />
            </div>
            <p className="text-xs font-medium text-slate-300">No documents found</p>
            <p className="text-[11px] text-slate-500 mt-1 max-w-sm mx-auto">
              Upload clinical PDF reports, genomics summaries, or lab notes to begin the indexing and ingestion pipeline.
            </p>
            {user?.role !== 'demo' && (
              <button
                onClick={() => setIsUploadOpen(true)}
                className="mt-4 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-teal-400 text-xs font-medium transition-colors border border-slate-700 inline-flex items-center space-x-1.5"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Upload First PDF</span>
              </button>
            )}
          </div>
        ) : (
          filteredDocs.map((doc) => {
            const badge = DOC_TYPE_LABELS[doc.doc_type] || DOC_TYPE_LABELS.patient_record;
            return (
              <div
                key={doc.id}
                className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 group"
              >
                <div className="flex items-start space-x-3 min-w-0">
                  <div className="p-2.5 rounded-xl bg-slate-800/80 text-teal-400 border border-slate-700/60 shrink-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2">
                      <h4 className="text-xs font-semibold text-white truncate max-w-sm">
                        {doc.title}
                      </h4>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${badge.color}`}
                      >
                        {badge.label}
                      </span>
                    </div>

                    <div className="flex items-center space-x-3 text-[11px] text-slate-400 mt-1">
                      <span>{formatFileSize(doc.file_size_bytes)}</span>
                      <span>•</span>
                      <span>Date: {doc.doc_date || 'Undated'}</span>
                      <span>•</span>
                      <span className="font-mono text-slate-500 text-[10px]">
                        SHA: {doc.file_hash_sha256.substring(0, 8)}...
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0 self-end sm:self-center">
                  {/* Status Badge */}
                  <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-xl bg-slate-900 border border-slate-800 text-[11px]">
                    {doc.ingestion_status === 'completed' ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
                        <span className="text-teal-400 font-medium">Indexed</span>
                      </>
                    ) : doc.ingestion_status === 'failed' ? (
                      <>
                        <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                        <span className="text-rose-400 font-medium">Failed</span>
                      </>
                    ) : (
                      <>
                        <Clock className="w-3.5 h-3.5 text-amber-400" />
                        <span className="text-amber-400 font-medium">Pending Parsing</span>
                      </>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => handleDownload(doc)}
                      title="Download Original PDF"
                      className="p-1.5 rounded-lg text-slate-400 hover:text-teal-300 hover:bg-slate-800 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    {user?.role === 'admin' && (
                      <button
                        onClick={() => handleDelete(doc.id)}
                        disabled={isDeletingId === doc.id}
                        title="Delete Document"
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors disabled:opacity-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
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
        onDocumentUploaded={() => {
          onRefresh();
        }}
      />
    </div>
  );
};
