import React, { useState, useRef } from 'react';
import { X, UploadCloud, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { Document, DocType } from '../../types';
import { useAuth } from '../auth/AuthContext';

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientId: string;
  patientName: string;
  onDocumentUploaded: (document: Document, isDuplicate?: boolean) => void;
}

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({
  isOpen,
  onClose,
  patientId,
  patientName,
  onDocumentUploaded,
}) => {
  const { token } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [docType, setDocType] = useState<DocType>('patient_record');
  const [docDate, setDocDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileSelection = (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setError('Only PDF documents (.pdf) are permitted.');
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setError('File exceeds maximum size ceiling of 25 MB.');
      return;
    }
    setSelectedFile(file);
    setError(null);
    if (!title) {
      // Clean filename for title
      setTitle(file.name.replace(/\.pdf$/i, ''));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a PDF document to upload.');
      return;
    }
    if (!title.trim()) {
      setError('Document title is required.');
      return;
    }

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('title', title.trim());
    formData.append('doc_type', docType);
    if (docDate) formData.append('doc_date', docDate);
    formData.append('patient_id', patientId);

    try {
      const response = await fetch('/api/v1/documents', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail?.message || errorData.detail || 'Failed to upload document.');
      }

      const created: Document = await response.json();
      onDocumentUploaded(created);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while uploading document.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Upload Clinical Document</h2>
              <p className="text-xs text-slate-400">
                Attaching to patient dossier: <span className="text-teal-400 font-medium">{patientName}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Dropzone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-5 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-teal-400 bg-teal-500/10'
                : selectedFile
                ? 'border-teal-500/50 bg-slate-950/60'
                : 'border-slate-800 hover:border-slate-700 bg-slate-950/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileSelection(e.target.files[0]);
                }
              }}
            />

            {selectedFile ? (
              <div className="flex items-center justify-center space-x-3 text-left">
                <div className="p-2 rounded-xl bg-teal-500/20 text-teal-300">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-white truncate max-w-[260px]">
                    {selectedFile.name}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • PDF Document
                  </div>
                </div>
                <CheckCircle2 className="w-5 h-5 text-teal-400 shrink-0 ml-auto" />
              </div>
            ) : (
              <div>
                <UploadCloud className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                <p className="text-xs font-medium text-slate-300">
                  Drag and drop PDF here, or <span className="text-teal-400">browse files</span>
                </p>
                <p className="text-[11px] text-slate-500 mt-1">
                  PDF format only (%PDF- header verified) • Maximum 25 MB
                </p>
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Document Title</label>
            <input
              type="text"
              required
              placeholder="e.g. FoundationOne CDx Genomic Profile Report"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-teal-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Document Type</label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value as DocType)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-teal-500"
              >
                <option value="patient_record">Patient Record / EHR</option>
                <option value="lab_report">Laboratory Report</option>
                <option value="discharge_summary">Discharge Summary</option>
                <option value="research_paper">Research Paper</option>
                <option value="clinical_guideline">Clinical Guideline</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Document Date</label>
              <input
                type="date"
                value={docDate}
                onChange={(e) => setDocDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>

          <div className="pt-3 flex items-center justify-end space-x-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isUploading}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUploading || !selectedFile}
              className="px-4 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 text-xs font-semibold shadow-lg shadow-teal-500/20 transition-all flex items-center space-x-1.5"
            >
              {isUploading ? (
                <span>Validating & Storing...</span>
              ) : (
                <>
                  <UploadCloud className="w-3.5 h-3.5" />
                  <span>Upload & Register</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
