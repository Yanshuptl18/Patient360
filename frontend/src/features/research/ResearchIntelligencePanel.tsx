import React, { useState, useEffect, useCallback } from 'react';
import {
  FileSearch,
  BookOpen,
  Filter,
  CheckCircle2,
  Copy,
  Check,
  Download,
  ExternalLink,
  Layers,
  Sparkles,
  AlertCircle,
  Loader2,
  RefreshCw,
  Search,
} from 'lucide-react';
import {
  ResearchStudy,
  StudyComparisonMatrix,
  EvidenceStrength,
  DossierExportResponse,
} from '../../types';
import { useAuth } from '../auth/AuthContext';

export const ResearchIntelligencePanel: React.FC = () => {
  const { token } = useAuth();
  const [studies, setStudies] = useState<ResearchStudy[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Selection
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDesign, setSelectedDesign] = useState<string>('all');
  const [selectedStudyIds, setSelectedStudyIds] = useState<string[]>([]);
  const [comparisonTopic, setComparisonTopic] = useState('Comparative Efficacy & Clinical Guideline Concordance');

  // Matrix & Export States
  const [matrix, setMatrix] = useState<StudyComparisonMatrix | null>(null);
  const [exportedDossier, setExportedDossier] = useState<DossierExportResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchStudies = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const url = new URL('/api/v1/research/studies', window.location.origin);
      if (searchQuery.trim()) url.searchParams.append('search', searchQuery.trim());
      if (selectedDesign !== 'all') url.searchParams.append('study_design', selectedDesign);

      const res = await fetch(url.toString(), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to load research studies.');
      const data: ResearchStudy[] = await res.json();
      setStudies(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown error loading studies.');
    } finally {
      setIsLoading(false);
    }
  }, [token, searchQuery, selectedDesign]);

  useEffect(() => {
    fetchStudies();
  }, [fetchStudies]);

  const toggleSelectStudy = (id: string) => {
    setSelectedStudyIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedStudyIds.length === studies.length) {
      setSelectedStudyIds([]);
    } else {
      setSelectedStudyIds(studies.map((s) => s.id));
    }
  };

  const handleGenerateMatrix = async () => {
    if (selectedStudyIds.length === 0 || isComparing || !token) return;
    setIsComparing(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/research/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          study_ids: selectedStudyIds,
          comparison_topic: comparisonTopic.trim() || undefined,
        }),
      });
      if (!res.ok) throw new Error('Failed to generate comparison matrix.');
      const data: StudyComparisonMatrix = await res.json();
      setMatrix(data);
      setExportedDossier(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Comparison failed.');
    } finally {
      setIsComparing(false);
    }
  };

  const handleExportDossier = async () => {
    if (selectedStudyIds.length === 0 || isExporting || !token) return;
    setIsExporting(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/research/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          study_ids: selectedStudyIds,
          comparison_topic: comparisonTopic.trim() || undefined,
          title: `Evidence Dossier: ${comparisonTopic.trim() || 'Biomedical Synthesis'}`,
        }),
      });
      if (!res.ok) throw new Error('Failed to export evidence dossier.');
      const data: DossierExportResponse = await res.json();
      setExportedDossier(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Dossier export failed.');
    } finally {
      setIsExporting(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadMarkdownFile = (filename: string, content: string) => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getEvidenceBadgeClass = (strength: EvidenceStrength) => {
    switch (strength) {
      case 'High':
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
      case 'Moderate':
        return 'bg-teal-500/15 text-teal-300 border-teal-500/30';
      case 'Low-Moderate':
        return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
      case 'Preliminary':
      default:
        return 'bg-slate-500/15 text-slate-300 border-slate-500/30';
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 rounded-3xl border border-slate-800 p-5 shadow-2xl overflow-hidden">
      {/* Panel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <FileSearch className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-bold text-white tracking-tight">Medical Research Intelligence</h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/20">
                Phase 11
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Multi-study methodology extraction • Side-by-side comparative matrices • Oxford CEBM evidence grading
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={fetchStudies}
            disabled={isLoading}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer border border-slate-700"
            title="Refresh Studies"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2 shrink-0">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Split Layout: Studies Explorer & Comparative Matrix / Dossier */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-5 py-4 overflow-hidden">
        {/* Left Column: Research Library & Filters (5 cols) */}
        <div className="lg:col-span-5 flex flex-col h-full overflow-hidden space-y-3">
          {/* Search & Filter Bar */}
          <div className="bg-slate-950/70 rounded-2xl border border-slate-800 p-3 space-y-2.5 shrink-0 shadow-inner">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by title, DOI, PMID, or author..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>

            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-1.5">
                <Filter className="w-3 h-3 text-slate-400" />
                <select
                  value={selectedDesign}
                  onChange={(e) => setSelectedDesign(e.target.value)}
                  className="bg-slate-900 border border-slate-800 text-slate-300 text-[11px] rounded-lg px-2 py-1 focus:outline-none focus:border-indigo-500"
                >
                  <option value="all">All Study Designs</option>
                  <option value="Randomized Controlled Trial">Randomized Controlled Trial</option>
                  <option value="Systematic Review & Meta-Analysis">Systematic Review & Meta-Analysis</option>
                  <option value="Clinical Practice Guideline">Clinical Practice Guideline</option>
                  <option value="Prospective Cohort Study">Prospective Cohort Study</option>
                  <option value="Retrospective Cohort Study">Retrospective Cohort Study</option>
                </select>
              </div>

              <button
                type="button"
                onClick={selectAll}
                className="text-[11px] text-indigo-400 hover:text-indigo-300 transition-colors font-medium cursor-pointer"
              >
                {selectedStudyIds.length === studies.length && studies.length > 0
                  ? 'Deselect All'
                  : `Select All (${studies.length})`}
              </button>
            </div>
          </div>

          {/* Studies List */}
          <div className="flex-1 min-h-0 bg-slate-950/70 rounded-2xl border border-slate-800 p-3 flex flex-col overflow-hidden">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/80 shrink-0">
              <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                <span>Indexed Clinical Studies</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                {selectedStudyIds.length} selected
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2.5 pt-2.5 pr-1">
              {isLoading ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 py-8">
                  <Loader2 className="w-6 h-6 animate-spin mb-2" />
                  <p className="text-xs">Loading research publications...</p>
                </div>
              ) : studies.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 py-8">
                  <BookOpen className="w-8 h-8 mb-2 text-slate-600" />
                  <p className="text-xs font-semibold text-slate-300">No Research Studies Indexed</p>
                  <p className="text-[11px] text-slate-500 mt-1 max-w-xs">
                    Upload clinical research papers or guidelines in the Documents tab to extract trial parameters.
                  </p>
                </div>
              ) : (
                studies.map((study) => {
                  const isChecked = selectedStudyIds.includes(study.id);
                  return (
                    <div
                      key={study.id}
                      onClick={() => toggleSelectStudy(study.id)}
                      className={`rounded-xl p-3 border transition-all cursor-pointer ${
                        isChecked
                          ? 'bg-indigo-500/10 border-indigo-500/40 shadow-sm shadow-indigo-500/10'
                          : 'bg-slate-900/80 border-slate-800/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start space-x-2.5">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => {}}
                            className="mt-0.5 rounded border-slate-700 bg-slate-900 text-indigo-500 focus:ring-0 focus:ring-offset-0 cursor-pointer"
                          />
                          <div>
                            <h4 className="text-xs font-semibold text-white leading-tight">
                              {study.title}
                            </h4>
                            {study.authors && (
                              <p className="text-[11px] text-slate-400 mt-0.5 italic">
                                {study.authors}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Parameter Badges */}
                      <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[10px]">
                        {study.study_design && (
                          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-indigo-300 border border-indigo-500/20 font-medium">
                            {study.study_design}
                          </span>
                        )}
                        {study.sample_size && (
                          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-teal-300 border border-teal-500/20 font-mono">
                            N = {study.sample_size.toLocaleString()}
                          </span>
                        )}
                        {study.doi && (
                          <span className="px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 font-mono border border-slate-800">
                            DOI: {study.doi}
                          </span>
                        )}
                        {study.pmid && (
                          <span className="px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 font-mono border border-slate-800">
                            PMID: {study.pmid}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Matrix Trigger Button */}
            <div className="pt-3 border-t border-slate-800/80 shrink-0">
              <button
                type="button"
                onClick={handleGenerateMatrix}
                disabled={selectedStudyIds.length === 0 || isComparing}
                className="w-full py-2 px-3 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-slate-950 font-bold text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isComparing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Synthesizing Comparative Matrix...</span>
                  </>
                ) : (
                  <>
                    <Layers className="w-4 h-4" />
                    <span>Compare Selected Studies ({selectedStudyIds.length})</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Comparative Matrix & Synthesis Dossier (7 cols) */}
        <div className="lg:col-span-7 flex flex-col h-full overflow-hidden space-y-3">
          {matrix ? (
            <div className="flex-1 flex flex-col min-h-0 bg-slate-950/70 rounded-2xl border border-slate-800 p-4 overflow-hidden">
              {/* Matrix Header & Actions */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2 shrink-0">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-white uppercase tracking-wider">
                      Evidence Comparison Matrix
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-indigo-500/20 text-indigo-300">
                      {matrix.studies_count} Studies Contrasted
                    </span>
                  </div>
                  <input
                    type="text"
                    value={comparisonTopic}
                    onChange={(e) => setComparisonTopic(e.target.value)}
                    placeholder="Enter comparison topic..."
                    className="text-xs text-slate-300 font-medium bg-transparent border-b border-slate-700/60 focus:outline-none focus:border-indigo-400 mt-1 w-full max-w-md"
                  />
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    type="button"
                    onClick={handleExportDossier}
                    disabled={isExporting}
                    className="px-3 py-1.5 rounded-xl bg-teal-500/15 hover:bg-teal-500/25 text-teal-300 border border-teal-500/30 text-xs font-semibold flex items-center space-x-1.5 transition-colors cursor-pointer disabled:opacity-50"
                  >
                    {isExporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                    <span>Export Dossier</span>
                  </button>
                </div>
              </div>

              {/* Scrollable Matrix Table & Findings */}
              <div className="flex-1 overflow-y-auto space-y-4 py-3 pr-1">
                {/* Side-by-Side Parameter Matrix */}
                <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 bg-slate-950 text-slate-400 font-mono text-[11px]">
                        <th className="py-2.5 px-3">Study / Publication</th>
                        <th className="py-2.5 px-3">Design & Level</th>
                        <th className="py-2.5 px-3">Sample (N)</th>
                        <th className="py-2.5 px-3">Population</th>
                        <th className="py-2.5 px-3">Interventions</th>
                        <th className="py-2.5 px-3">Primary Endpoint</th>
                        <th className="py-2.5 px-3">Limitations</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-300 text-[11px]">
                      {matrix.matrix_rows.map((row, idx) => (
                        <tr key={row.study_id} className="hover:bg-slate-850/50 transition-colors">
                          <td className="py-3 px-3 font-medium text-white max-w-[180px]">
                            <div className="font-semibold text-slate-100 line-clamp-2">
                              [{idx + 1}] {row.title}
                            </div>
                            {row.doi && (
                              <a
                                href={`https://doi.org/${row.doi}`}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center space-x-1 text-[10px] text-indigo-400 hover:text-indigo-300 font-mono mt-1"
                              >
                                <span>DOI Link</span>
                                <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            )}
                          </td>
                          <td className="py-3 px-3 whitespace-nowrap">
                            <span className="block font-medium text-slate-200">
                              {row.study_design || 'Observational'}
                            </span>
                            <span
                              className={`inline-block mt-1 px-1.5 py-0.5 rounded border text-[10px] font-bold ${getEvidenceBadgeClass(
                                row.evidence_strength
                              )}`}
                            >
                              Level: {row.evidence_strength}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-mono font-bold text-teal-300 whitespace-nowrap">
                            {row.sample_size ? row.sample_size.toLocaleString() : 'N/A'}
                          </td>
                          <td className="py-3 px-3 max-w-[160px] line-clamp-3 text-slate-400">
                            {row.population || 'Standard cohort'}
                          </td>
                          <td className="py-3 px-3 max-w-[160px] line-clamp-3 text-slate-300">
                            {row.intervention || 'Standard regimen'}
                          </td>
                          <td className="py-3 px-3 max-w-[180px] line-clamp-3 text-emerald-300/90">
                            {row.primary_outcome || 'Clinical endpoints'}
                          </td>
                          <td className="py-3 px-3 max-w-[160px] line-clamp-3 text-slate-500 italic">
                            {row.limitations || 'Not reported'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Synthesis & Guideline Alignment Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                    <span className="text-[11px] font-bold text-indigo-300 uppercase tracking-wider flex items-center space-x-1">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Cross-Study Synthesis</span>
                    </span>
                    <p className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {matrix.synthesized_findings}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                    <span className="text-[11px] font-bold text-teal-300 uppercase tracking-wider flex items-center space-x-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Clinical Guideline Concordance</span>
                    </span>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {matrix.guideline_alignment}
                    </p>
                  </div>
                </div>

                {/* Exported Dossier Preview Banner */}
                {exportedDossier && (
                  <div className="p-4 rounded-xl bg-teal-500/10 border border-teal-500/20 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-teal-300">
                        <CheckCircle2 className="w-4 h-4" />
                        <span className="text-xs font-bold">{exportedDossier.title}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={() => copyToClipboard(exportedDossier.markdown_content)}
                          className="px-2.5 py-1 rounded-lg bg-slate-900 text-teal-300 hover:text-white text-xs font-medium flex items-center space-x-1 border border-teal-500/30 transition-colors"
                        >
                          {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                          <span>{copied ? 'Copied' : 'Copy Markdown'}</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => downloadMarkdownFile('clinical_evidence_dossier.md', exportedDossier.markdown_content)}
                          className="px-2.5 py-1 rounded-lg bg-teal-500 text-slate-950 font-bold text-xs flex items-center space-x-1 transition-all shadow-md shadow-teal-500/20"
                        >
                          <Download className="w-3 h-3" />
                          <span>Download .MD</span>
                        </button>
                      </div>
                    </div>
                    <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 text-[11px] font-mono max-h-48 overflow-y-auto whitespace-pre-wrap">
                      {exportedDossier.markdown_content}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 bg-slate-950/70 rounded-2xl border border-slate-800 p-8 flex flex-col items-center justify-center text-center">
              <Layers className="w-12 h-12 text-slate-700 mb-3" />
              <h3 className="text-sm font-semibold text-white">No Studies Contrasted Yet</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm">
                Select one or more research publications on the left and click "Compare Selected Studies" to build an evidence matrix.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
