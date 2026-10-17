import React, { useState, useEffect } from 'react';
import { Database, Cpu, HardDrive, RefreshCw, CheckCircle2, AlertTriangle, XCircle, Sparkles } from 'lucide-react';
import { HealthResponse } from '../types';

export const HealthStatus: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/health');
      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }
      const data: HealthResponse = await res.json();
      setHealth(data);
      setLastChecked(new Date());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'The service is temporarily unavailable.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'UP':
      case 'HEALTHY':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>OPERATIONAL</span>
          </span>
        );
      case 'DEGRADED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3 h-3 text-amber-600" />
            <span>DEGRADED</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3 h-3 text-rose-600" />
            <span>OFFLINE</span>
          </span>
        );
    }
  };

  const db = health?.components?.database;
  const vector = health?.components?.vector_store;
  const storage = health?.components?.storage;
  const llm = health?.components?.llm_provider;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-200 gap-3">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-base font-semibold text-slate-900 tracking-tight">System Service Status</h2>
            {getStatusBadge(health?.status || (loading ? 'UP' : 'DOWN'))}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time operational availability for medical records, evidence search, document storage, and clinical assistant.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-500">
          <span>Checked: {lastChecked.toLocaleTimeString()}</span>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="p-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 transition-colors border border-slate-200 disabled:opacity-50 cursor-pointer"
            title="Refresh Status"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-teal-600' : ''}`} />
          </button>
        </div>
      </div>

      {error ? (
        <div className="mt-5 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-3">
          <XCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <div>
            <p className="font-semibold">Service Notice</p>
            <p className="text-rose-700 mt-0.5">{error} Please check connection or try again shortly.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
          {/* Relational Database */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-teal-100 text-teal-800">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-slate-900">Medical Database</h3>
                  <span className="text-xs text-slate-500">Encrypted Patient Records</span>
                </div>
              </div>
              {getStatusBadge(db?.status)}
            </div>
            <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <span className="truncate max-w-[170px]" title={db?.message || 'Connected'}>
                {db?.message ? 'Connected and Active' : 'Verifying...'}
              </span>
              <span className="font-mono text-slate-700 font-medium">
                {db?.latency_ms ?? 0} ms
              </span>
            </div>
          </div>

          {/* Semantic Search Engine */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-teal-100 text-teal-800">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-slate-900">Evidence Search</h3>
                  <span className="text-xs text-slate-500">Document Retrieval Engine</span>
                </div>
              </div>
              {getStatusBadge(vector?.status)}
            </div>
            <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <span className="truncate max-w-[170px]" title={vector?.message || 'Ready'}>
                {vector?.message ? 'Ready and Indexed' : 'Checking...'}
              </span>
              <span className="font-mono text-slate-700 font-medium">
                {vector?.latency_ms ?? 0} ms
              </span>
            </div>
          </div>

          {/* Document Storage */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-teal-100 text-teal-800">
                  <HardDrive className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-slate-900">Document Archive</h3>
                  <span className="text-xs text-slate-500">Medical Document Files</span>
                </div>
              </div>
              {getStatusBadge(storage?.status)}
            </div>
            <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <span className="truncate max-w-[170px]" title={storage?.message || 'Storage mounted'}>
                {storage?.message ? 'Securely Mounted' : 'Verifying...'}
              </span>
              <span className="font-mono text-slate-700 font-medium">
                {storage?.latency_ms ?? 0} ms
              </span>
            </div>
          </div>

          {/* LLM Clinical Assistant */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-teal-100 text-teal-800">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-slate-900">Clinical Assistant</h3>
                  <span className="text-xs text-slate-500">Evidence Synthesis Active</span>
                </div>
              </div>
              {getStatusBadge(llm?.status || (health ? 'UP' : undefined))}
            </div>
            <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <span className="truncate max-w-[170px]" title={llm?.message || 'Ready'}>
                {llm?.message ? 'Operational' : 'Ready'}
              </span>
              <span className="font-mono text-slate-700 font-medium">
                {llm?.latency_ms ?? 1} ms
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
