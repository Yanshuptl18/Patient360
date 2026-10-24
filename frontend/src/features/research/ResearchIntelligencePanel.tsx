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

  // Filters and selection
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDesign, setSelectedDesign] = useState<string>('all');
  const [selectedStudyIds, setSelectedStudyIds] = useState<string[]>([]);
  const [comparisonTopic, setComparisonTopic] = useState('Comparative Efficacy and Clinical Guideline Concordance');

  // Matrix and export
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
      if (!res.ok) throw new Error('Failed to load clinical research studies.');
      const data: ResearchStudy[] = await res.json();
      setStudies(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to retrieve research studies.');
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
      if (!res.ok) throw new Error('Failed to generate study comparison.');
      const data: StudyComparisonMatrix = await res.json();
      setMatrix(data);
      setExportedDossier(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Comparison synthesis failed.');
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
          title: `Evidence Summary: ${comparisonTopic.trim() || 'Biomedical Synthesis'}`,
        }),
      });
      if (!res.ok) throw new Error('Failed to export evidence summary.');
      const data: DossierExportResponse = await res.json();
      setExportedDossier(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Evidence summary export failed.');
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
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Moderate':
        return 'bg-teal-50 text-teal-700 border-teal-200';
      case 'Low-Moderate':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'Preliminary':
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="flex flex-col min-h-[640px] bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
      {/* Panel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 gap-3 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-teal-50 text-teal-700 border border-teal-200">
            <FileSearch className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-semibold text-slate-900 tracking-tight">Biomedical Research Workspace</h2>
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-teal-50 text-teal-700 border border-teal-200">
                Comparative Studies
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Multi-study methodology extraction • Side-by-side study comparison • Evidence quality grading
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={fetchStudies}
            disabled={isLoading}
            className="p-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 transition-colors cursor-pointer border border-slate-200"
            title="Refresh Studies"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-3 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2 shrink-0">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Split Layout: Studies Explorer & Comparative Matrix */}
      <div className="flex-1 min-h-[540px] grid grid-cols-1 lg:grid-cols-12 gap-5 py-4">
        {/* Left Column: Research Library & Filters */}
        <div className="lg:col-span-5 flex flex-col h-full overflow-hidden space-y-3">
          {/* Search and Filters */}
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-3 space-y-2.5 shrink-0">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by title, DOI, PMID, or author..."
                className="w-full bg-white border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500 transition-colors"
              />
            </div>

            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-1.5">
                <Filter className="w-3.5 h-3.5 text-slate-500" />
                <select
                  value={selectedDesign}
                  onChange={(e) => setSelectedDesign(e.target.value)}
                  className="bg-white border border-slate-200 text-slate-700 text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-teal-500"
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
                className="text-xs text-teal-600 hover:text-teal-700 transition-colors font-medium cursor-pointer"
              >
                {selectedStudyIds.length === studies.length && studies.length > 0
                  ? 'Deselect All'
                  : `Select All (${studies.length})`}
              </button>
            </div>
          </div>

          {/* Studies List */}
          <div className="flex-1 min-h-0 bg-slate-50/50 rounded-xl border border-slate-200 p-3 flex flex-col overflow-hidden">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200 shrink-0">
              <span className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
                <BookOpen className="w-3.5 h-3.5 text-teal-600" />
                <span>Available Research Studies</span>
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
                {selectedStudyIds.length} selected
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pt-2 pr-1">
              {isLoading ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-400 py-8">
                  <Loader2 className="w-5 h-5 animate-spin mb-2" />
                  <p className="text-xs">Loading publications...</p>
                </div>
              ) : studies.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 py-8">
                  <BookOpen className="w-8 h-8 mb-2 text-slate-300" />
                  <p className="text-xs font-semibold text-slate-700">No Research Studies Found</p>
                  <p className="text-xs text-slate-500 mt-1 max-w-xs">
                    Upload clinical research papers or clinical guidelines in the Documents tab to extract study parameters.
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
                          ? 'bg-teal-50/70 border-teal-400 shadow-sm'
                          : 'bg-white border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-start space-x-2.5">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500 cursor-pointer"
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="text-xs font-semibold text-slate-900 leading-snug">
                            {study.title}
                          </h4>
                          {study.authors && (
                            <p className="text-xs text-slate-500 mt-0.5 italic">
                              {study.authors}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Parameter Badges */}
                      <div className="mt-2 pl-6 flex flex-wrap items-center gap-1.5 text-xs">
                        {study.study_design && (
                          <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 font-medium">
                            {study.study_design}
                          </span>
                        )}
                        {study.sample_size && (
                          <span className="px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200 font-medium">
                            N = {study.sample_size.toLocaleString()}
                          </span>
                        )}
                        {study.doi && (
                          <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 font-mono text-[11px]">
                            DOI: {study.doi}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Matrix Trigger Button */}
            <div className="pt-3 border-t border-slate-200 shrink-0">
              <button
                type="button"
                onClick={handleGenerateMatrix}
                disabled={selectedStudyIds.length === 0 || isComparing}
                className="w-full py-2 px-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-medium text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isComparing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Comparing Studies...</span>
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

        {/* Right Column: Comparative Matrix & Synthesis */}
        <div className="lg:col-span-7 flex flex-col h-full overflow-hidden space-y-3">
          {matrix ? (
            <div className="flex-1 flex flex-col min-h-0 bg-white rounded-xl border border-slate-200 p-4 overflow-hidden shadow-sm">
              {/* Matrix Header & Actions */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-200 gap-2 shrink-0">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                      Study Findings Comparison
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-teal-50 text-teal-700 border border-teal-200">
                      {matrix.studies_count} Studies Contrasted
                    </span>
                  </div>
                  <input
                    type="text"
                    value={comparisonTopic}
                    onChange={(e) => setComparisonTopic(e.target.value)}
                    placeholder="Enter comparison topic..."
                    className="text-xs text-slate-700 font-medium bg-transparent border-b border-slate-300 focus:outline-none focus:border-teal-500 mt-1 w-full max-w-md"
                  />
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    type="button"
                    onClick={handleExportDossier}
                    disabled={isExporting}
                    className="px-3 py-1.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 border border-teal-200 text-xs font-medium flex items-center space-x-1.5 transition-colors cursor-pointer disabled:opacity-50"
                  >
                    {isExporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                    <span>Export Evidence Summary</span>
                  </button>
                </div>
              </div>

              {/* Scrollable Matrix Table & Findings */}
              <div className="flex-1 overflow-y-auto space-y-4 py-3 pr-1">
                {/* Table */}
                <div className="overflow-x-auto rounded-xl border border-slate-200">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-medium">
                        <th className="py-2.5 px-3">Study / Publication</th>
                        <th className="py-2.5 px-3">Design & Level</th>
                        <th className="py-2.5 px-3">Sample (N)</th>
                        <th className="py-2.5 px-3">Population</th>
                        <th className="py-2.5 px-3">Interventions</th>
                        <th className="py-2.5 px-3">Primary Endpoint</th>
                        <th className="py-2.5 px-3">Limitations</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 text-slate-700">
                      {matrix.matrix_rows.map((row, idx) => (
                        <tr key={row.study_id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-3 px-3 font-medium text-slate-900 max-w-[180px]">
                            <div className="font-semibold text-slate-800 line-clamp-2">
                              [{idx + 1}] {row.title}
                            </div>
                            {row.doi && (
                              <a
                                href={`https://doi.org/${row.doi}`}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center space-x-1 text-xs text-teal-600 hover:text-teal-700 font-medium mt-1"
                              >
                                <span>DOI Link</span>
                                <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            )}
                          </td>
                          <td className="py-3 px-3 whitespace-nowrap">
                            <span className="block font-medium text-slate-800">
                              {row.study_design || 'Observational'}
                            </span>
                            <span
                              className={`inline-block mt-1 px-1.5 py-0.5 rounded border text-[11px] font-medium ${getEvidenceBadgeClass(
                                row.evidence_strength
                              )}`}
                            >
                              Level: {row.evidence_strength}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-medium text-teal-700 whitespace-nowrap">
                            {row.sample_size ? row.sample_size.toLocaleString() : 'N/A'}
                          </td>
                          <td className="py-3 px-3 max-w-[160px] line-clamp-3 text-slate-600">
                            {row.population || 'Standard cohort'}
                          </td>
                          <td className="py-3 px-3 max-w-[160px] line-clamp-3 text-slate-700">
                            {row.intervention || 'Standard regimen'}
                          </td>
                          <td className="py-3 px-3 max-w-[180px] line-clamp-3 text-slate-900 font-medium">
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
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                    <span className="text-xs font-semibold text-teal-700 uppercase tracking-wider flex items-center space-x-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Cross-Study Synthesis</span>
                    </span>
                    <p className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed">
                      {matrix.synthesized_findings}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                    <span className="text-xs font-semibold text-teal-700 uppercase tracking-wider flex items-center space-x-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Clinical Guideline Concordance</span>
                    </span>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      {matrix.guideline_alignment}
                    </p>
                  </div>
                </div>

                {/* Exported Evidence Summary Preview Banner */}
                {exportedDossier && (
                  <div className="p-4 rounded-xl bg-teal-50/70 border border-teal-200 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-teal-800">
                        <CheckCircle2 className="w-4 h-4" />
                        <span className="text-xs font-semibold">{exportedDossier.title}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={() => copyToClipboard(exportedDossier.markdown_content)}
                          className="px-2.5 py-1 rounded-lg bg-white text-slate-700 hover:text-slate-900 text-xs font-medium flex items-center space-x-1 border border-slate-200 transition-colors"
                        >
                          {copied ? <Check className="w-3 h-3 text-teal-600" /> : <Copy className="w-3 h-3" />}
                          <span>{copied ? 'Copied' : 'Copy Markdown'}</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => downloadMarkdownFile('evidence_summary.md', exportedDossier.markdown_content)}
                          className="px-2.5 py-1 rounded-lg bg-teal-600 text-white font-medium text-xs flex items-center space-x-1 transition-all shadow-sm hover:bg-teal-700"
                        >
                          <Download className="w-3 h-3" />
                          <span>Download .MD</span>
                        </button>
                      </div>
                    </div>
                    <pre className="p-3 bg-white border border-slate-200 rounded-lg text-slate-700 text-xs font-mono max-h-48 overflow-y-auto whitespace-pre-wrap">
                      {exportedDossier.markdown_content}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 bg-slate-50/50 rounded-xl border border-slate-200 p-8 flex flex-col items-center justify-center text-center">
              <Layers className="w-10 h-10 text-slate-300 mb-3" />
              <h3 className="text-sm font-semibold text-slate-800">No Studies Contrasted Yet</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Select one or more research publications on the left and select "Compare Selected Studies" to build an evidence summary.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
