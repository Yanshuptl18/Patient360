import React, { useState, useEffect, useCallback } from 'react';
import {
  Users,
  Search,
  UserPlus,
  FileText,
  Calendar,
  AlertCircle,
  Activity,
  ChevronRight,
  Shield,
} from 'lucide-react';
import { Patient } from '../../types';
import { useAuth } from '../auth/AuthContext';
import { CreatePatientModal } from './CreatePatientModal';

interface PatientListProps {
  selectedPatientId: string | null;
  onSelectPatient: (patient: Patient) => void;
}

export const PatientList: React.FC<PatientListProps> = ({
  selectedPatientId,
  onSelectPatient,
}) => {
  const { token, user } = useAuth();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const fetchPatients = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const url = search ? `/api/v1/patients?search=${encodeURIComponent(search)}` : '/api/v1/patients';
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('We could not load the patient records.');
      }

      const data: Patient[] = await response.json();
      setPatients(data);

      // Auto-select first patient if none currently selected
      if (data.length > 0 && !selectedPatientId) {
        onSelectPatient(data[0]);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('We could not load the patient records.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [token, search, selectedPatientId, onSelectPatient]);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  const handlePatientCreated = (newPatient: Patient) => {
    setPatients((prev) => [newPatient, ...prev]);
    onSelectPatient(newPatient);
  };

  return (
    <div className="rounded-3xl bg-white border border-slate-200 p-6 flex flex-col h-full shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-teal-50 text-teal-700 border border-teal-200">
            <Users className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Authorized Patient Records</h2>
            <p className="text-[11px] text-slate-500">
              Access-controlled cohort • {patients.length} accessible
            </p>
          </div>
        </div>

        {user?.role !== 'demo' && user?.role !== 'patient' && (
          <button
            onClick={() => setIsCreateOpen(true)}
            className="px-2.5 py-1.5 rounded-xl bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 transition-all text-xs font-semibold flex items-center space-x-1 cursor-pointer"
            title="Register Patient Dossier"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Add Patient</span>
          </button>
        )}
      </div>

      {/* Search Input */}
      <div className="mt-4 relative">
        <input
          type="text"
          placeholder="Filter by name, identifier, or condition..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-2 pl-8 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 text-xs placeholder-slate-400 focus:outline-none focus:border-teal-600 focus:bg-white transition-colors"
        />
        <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5 pointer-events-none" />
      </div>

      {/* Patient List Container */}
      <div className="flex-1 overflow-y-auto mt-4 space-y-2.5 pr-1">
        {isLoading ? (
          <div className="py-10 text-center text-xs text-slate-500">Loading authorized patient records...</div>
        ) : error ? (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        ) : patients.length === 0 ? (
          <div className="py-10 text-center">
            <Shield className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="text-xs font-medium text-slate-700">No authorized patients found</p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {search ? 'Try adjusting your search criteria.' : 'No records exist in this authorized cohort.'}
            </p>
          </div>
        ) : (
          patients.map((p) => {
            const isSelected = p.id === selectedPatientId;
            return (
              <div
                key={p.id}
                onClick={() => onSelectPatient(p)}
                className={`p-3.5 rounded-2xl cursor-pointer transition-all border ${
                  isSelected
                    ? 'bg-teal-50/80 border-teal-300 shadow-xs'
                    : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/60'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-slate-900">
                        {p.first_name} {p.last_name}
                      </span>
                      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                        {p.mrn_synthetic}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] text-slate-500 mt-1">
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        <span>DOB: {p.date_of_birth}</span>
                      </span>
                      <span>•</span>
                      <span>{p.gender}</span>
                    </div>

                    {p.primary_condition && (
                      <div className="flex items-center space-x-1 text-[11px] text-teal-700 mt-1.5 font-medium">
                        <Activity className="w-3 h-3 shrink-0" />
                        <span className="truncate max-w-[200px]">{p.primary_condition}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col items-end space-y-2 shrink-0">
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-[10px] text-slate-700 font-medium">
                      <FileText className="w-3 h-3 text-teal-700" />
                      <span>{p.document_count ?? 0}</span>
                    </span>
                    <ChevronRight
                      className={`w-4 h-4 transition-transform ${
                        isSelected ? 'text-teal-700 translate-x-0.5' : 'text-slate-400'
                      }`}
                    />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Creation Modal */}
      <CreatePatientModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onPatientCreated={handlePatientCreated}
      />
    </div>
  );
};
