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
        throw new Error('Failed to fetch patient records.');
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
        setError('Error fetching patient records.');
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
    <div className="rounded-3xl bg-slate-900/60 border border-slate-800 p-6 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-teal-500/10 text-teal-400">
            <Users className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Authorized Patient Dossiers</h2>
            <p className="text-[11px] text-slate-400">
              Server-enforced cohort isolation • {patients.length} accessible
            </p>
          </div>
        </div>

        {user?.role !== 'demo' && (
          <button
            onClick={() => setIsCreateOpen(true)}
            className="p-1.5 rounded-xl bg-teal-500/10 hover:bg-teal-500/20 text-teal-400 border border-teal-500/30 transition-all text-xs font-medium flex items-center space-x-1"
            title="Register Synthetic Patient"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Patient</span>
          </button>
        )}
      </div>

      {/* Search Input */}
      <div className="mt-4 relative">
        <input
          type="text"
          placeholder="Filter by name, MRN, or condition..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-2 pl-8 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-teal-500"
        />
        <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-3 pointer-events-none" />
      </div>

      {/* Patient List Container */}
      <div className="flex-1 overflow-y-auto mt-4 space-y-2.5 pr-1">
        {isLoading ? (
          <div className="py-10 text-center text-xs text-slate-500">Loading authorized records...</div>
        ) : error ? (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : patients.length === 0 ? (
          <div className="py-10 text-center">
            <Shield className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-xs text-slate-400">No authorized patients found</p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {search ? 'Try adjusting your search criteria.' : 'Create a synthetic patient dossier to begin.'}
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
                    ? 'bg-teal-500/10 border-teal-500/40 shadow-lg shadow-teal-500/5'
                    : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/40'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-semibold text-white">
                        {p.first_name} {p.last_name}
                      </span>
                      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                        {p.mrn_synthetic}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-1">
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3 text-slate-500" />
                        <span>DOB: {p.date_of_birth}</span>
                      </span>
                      <span>•</span>
                      <span>{p.gender}</span>
                    </div>

                    {p.primary_condition && (
                      <div className="flex items-center space-x-1 text-[11px] text-teal-400/90 mt-1.5 font-medium">
                        <Activity className="w-3 h-3 shrink-0" />
                        <span className="truncate max-w-[200px]">{p.primary_condition}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col items-end space-y-2 shrink-0">
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-slate-900 border border-slate-800 text-[10px] text-slate-300">
                      <FileText className="w-3 h-3 text-teal-400" />
                      <span>{p.document_count ?? 0}</span>
                    </span>
                    <ChevronRight
                      className={`w-4 h-4 transition-transform ${
                        isSelected ? 'text-teal-400 translate-x-0.5' : 'text-slate-600'
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
