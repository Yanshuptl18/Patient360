import React, { useState } from 'react';
import { Patient, Document } from '../../types';
import { DocumentList } from '../documents/DocumentList';
import { ClinicalRAGPanel } from '../rag/ClinicalRAGPanel';
import { ClinicalTimelinePanel } from '../timeline/ClinicalTimelinePanel';
import {
  User,
  Heart,
  FileText,
  Clock,
  MessageSquare,
  ShieldCheck,
  Calendar,
  Info,
} from 'lucide-react';

interface PatientPortalProps {
  patient: Patient;
  documents: Document[];
  onRefreshDocuments: () => void;
}

export const PatientPortal: React.FC<PatientPortalProps> = ({
  patient,
  documents,
  onRefreshDocuments,
}) => {
  const [activeTab, setActiveTab] = useState<'documents' | 'timeline' | 'rag'>('documents');

  return (
    <div className="space-y-6">
      {/* Patient Profile Card */}
      <div className="rounded-2xl bg-white border border-slate-200 p-6 sm:p-7 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start sm:items-center space-x-4">
            <div className="w-14 h-14 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 shrink-0">
              <User className="w-7 h-7" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                  {patient.first_name} {patient.last_name}
                </h2>
                <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
                  Record ID: {patient.mrn_synthetic}
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
                  Active Patient Record
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 mt-2">
                <span className="flex items-center space-x-1.5">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>Date of Birth: {patient.date_of_birth}</span>
                </span>
                <span>•</span>
                <span>Biological Sex: {patient.gender}</span>
                {patient.primary_condition && (
                  <>
                    <span>•</span>
                    <span className="flex items-center space-x-1 text-teal-700 font-medium">
                      <Heart className="w-3.5 h-3.5 text-teal-600" />
                      <span>{patient.primary_condition}</span>
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row md:flex-col items-start md:items-end gap-1.5 text-xs text-slate-500 border-t md:border-t-0 pt-4 md:pt-0 border-slate-200">
            <div className="flex items-center space-x-1.5 text-emerald-700 font-medium">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Isolated Personal Portal</span>
            </div>
            <p className="text-xs text-slate-500 max-w-xs text-left md:text-right">
              Access is strictly confined to your personal authorized medical records.
            </p>
          </div>
        </div>

        {/* Informational Banner */}
        <div className="mt-5 p-3 rounded-xl bg-teal-50/70 border border-teal-200 flex items-start space-x-3 text-xs text-teal-900">
          <Info className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-900">Personal Record Overview:</span> You are viewing your personal care record. You can review verified medical documents, track your history of care events and medications, or ask questions grounded in your records.
          </div>
        </div>
      </div>

      {/* Patient Tab Navigation */}
      <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl border border-slate-200 w-fit">
        <button
          type="button"
          onClick={() => setActiveTab('documents')}
          className={`px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
            activeTab === 'documents'
              ? 'bg-white text-teal-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>My Medical Documents ({documents.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('timeline')}
          className={`px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
            activeTab === 'timeline'
              ? 'bg-white text-teal-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          <span>My Medical History Timeline</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('rag')}
          className={`px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
            activeTab === 'rag'
              ? 'bg-white text-teal-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Ask About My Records</span>
        </button>
      </div>

      {/* Patient Tab Content */}
      <div className="min-h-[640px]">
        {activeTab === 'documents' ? (
          <DocumentList
            patientId={patient.id}
            patientName={`${patient.first_name} ${patient.last_name}`}
            documents={documents}
            onRefresh={onRefreshDocuments}
          />
        ) : activeTab === 'timeline' ? (
          <ClinicalTimelinePanel
            patientId={patient.id}
            patientName={`${patient.first_name} ${patient.last_name}`}
          />
        ) : (
          <ClinicalRAGPanel
            patientId={patient.id}
            patientName={`${patient.first_name} ${patient.last_name}`}
          />
        )}
      </div>
    </div>
  );
};
