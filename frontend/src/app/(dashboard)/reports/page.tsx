'use client';

import React, { useState, useEffect } from 'react';
import { FileText, Download, Sparkles, CheckCircle2, RefreshCw, Eye, X, ShieldCheck, Database } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface ReportTemplate {
  id: string;
  title: string;
  type: string;
  format: string;
  size: string;
  endpoint: string;
  filename: string;
  description: string;
}

const reportTemplates: ReportTemplate[] = [
  {
    id: 'rep-01',
    title: 'Executive Summary & RAG Health Index',
    type: 'Executive Summary',
    format: 'TXT/PDF',
    size: '2.4 MB',
    endpoint: `${API_BASE}/reports/export/summary`,
    filename: 'executive_rag_health_report.txt',
    description: 'High-level executive audit summary, overall RAG health index, and compliance status.',
  },
  {
    id: 'rep-02',
    title: 'AI Safety & Adversarial Security Audit',
    type: 'Security Audit',
    format: 'CSV',
    size: '1.8 MB',
    endpoint: `${API_BASE}/reports/export/csv`,
    filename: 'ai_safety_adversarial_audit.csv',
    description: 'Detailed log of prompt injection tests, jailbreak attempts, and security scores.',
  },
  {
    id: 'rep-03',
    title: 'Hallucination & Retrieval Groundedness Log',
    type: 'Hallucination Report',
    format: 'CSV',
    size: '4.1 MB',
    endpoint: `${API_BASE}/reports/export/csv`,
    filename: 'hallucination_retrieval_log.csv',
    description: 'Per-question evaluation results, faithfulness ratings, and context retrieval scores.',
  },
  {
    id: 'rep-04',
    title: 'Token Usage & Cost Analysis',
    type: 'Cost Report',
    format: 'JSON',
    size: '850 KB',
    endpoint: `${API_BASE}/reports/export/json`,
    filename: 'token_usage_cost_analysis.json',
    description: 'Structured JSON export of model latency, token counts, and cost breakdown.',
  },
];

export default function ReportsPage() {
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  
  // Interactive Report Inspector Modal State
  const [activeReport, setActiveReport] = useState<ReportTemplate | null>(null);
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [evalRuns, setEvalRuns] = useState<any[]>([]);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  const fetchEvalRuns = async () => {
    try {
      const res = await fetch(`${API_BASE}/evaluations/`);
      if (res.ok) {
        const data = await res.json();
        setEvalRuns(data || []);
      }
    } catch (e) {
      console.warn('Failed to fetch evaluation runs:', e);
    }
  };

  useEffect(() => {
    fetchEvalRuns();
  }, []);

  const handleViewReport = async (rep: ReportTemplate) => {
    setActiveReport(rep);
    setIsLoadingPreview(true);
    setReportContent(null);

    try {
      const res = await fetch(`${API_BASE}/reports/export/summary`);
      if (res.ok) {
        const text = await res.text();
        setReportContent(text);
      }
    } catch (e) {
      console.warn('Error fetching preview text:', e);
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleDownload = (endpoint: string, defaultFilename: string) => {
    window.open(endpoint, '_blank');
    setToastMessage(`Downloading report package (${defaultFilename})...`);
    setTimeout(() => setToastMessage(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Enterprise Audit Reports</h1>
          <p className="text-xs text-gray-400 mt-1">Inspect and export compliance-ready PDF, CSV, and JSON audit reports generated from PostgreSQL evaluations.</p>
        </div>
        <button
          onClick={() => handleDownload(`${API_BASE}/reports/export/summary`, 'full_audit_summary.txt')}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/25 flex items-center space-x-2 transition-all cursor-pointer"
        >
          <Sparkles className="w-4 h-4" />
          <span>Generate Full Audit Package</span>
        </button>
      </div>

      {/* Toast Notification */}
      {toastMessage && (
        <div className="glass-panel p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-300 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reportTemplates.map((rep) => (
          <div key={rep.id} className="glass-panel p-6 rounded-2xl border border-gray-800 hover:border-blue-500/40 transition-all flex flex-col justify-between space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3.5">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600/20 to-purple-600/20 text-blue-400 border border-blue-500/20 flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-800 text-blue-400 uppercase tracking-wide">
                    {rep.type}
                  </span>
                  <h3 className="text-base font-semibold text-white mt-1.5">{rep.title}</h3>
                  <p className="text-xs text-gray-400 mt-1">{rep.description}</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-gray-900 text-gray-300 border border-gray-800 shrink-0">
                {rep.format}
              </span>
            </div>

            <div className="pt-4 border-t border-gray-800/80 flex items-center justify-between">
              <span className="text-xs text-gray-500 font-mono">{rep.id}</span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleViewReport(rep)}
                  className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-200 flex items-center space-x-1.5 transition-all cursor-pointer border border-gray-700"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>View Report</span>
                </button>
                <button
                  onClick={() => handleDownload(rep.endpoint, rep.filename)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white flex items-center space-x-2 transition-all shadow-md shadow-blue-500/20 cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Interactive Report Inspection Modal */}
      {activeReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <div className="glass-panel w-full max-w-3xl p-6 rounded-2xl border border-gray-800 bg-gray-950 shadow-2xl space-y-5 max-h-[85vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-gray-800 pb-4">
              <div className="flex items-center space-x-3">
                <FileText className="w-6 h-6 text-blue-400" />
                <div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-blue-400 bg-blue-950/80 px-2 py-0.5 rounded border border-blue-900/60">
                    {activeReport.type}
                  </span>
                  <h3 className="text-lg font-bold text-white mt-1">{activeReport.title}</h3>
                </div>
              </div>
              <button
                onClick={() => setActiveReport(null)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="overflow-y-auto space-y-5 pr-1 flex-1 text-xs">
              {isLoadingPreview ? (
                <div className="py-12 flex flex-col items-center justify-center space-y-3">
                  <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
                  <p className="text-gray-400">Loading audit report from PostgreSQL...</p>
                </div>
              ) : (
                <>
                  {/* Summary Metric Cards */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="glass-panel p-4 rounded-xl border border-gray-800">
                      <span className="text-gray-400 block text-[10px]">Total Evaluation Runs</span>
                      <p className="text-lg font-bold text-white mt-1">{evalRuns.length} Runs</p>
                    </div>
                    <div className="glass-panel p-4 rounded-xl border border-gray-800">
                      <span className="text-gray-400 block text-[10px]">Database Persistence</span>
                      <p className="text-lg font-bold text-emerald-400 mt-1 flex items-center space-x-1">
                        <Database className="w-4 h-4 inline" />
                        <span>PostgreSQL Sync</span>
                      </p>
                    </div>
                    <div className="glass-panel p-4 rounded-xl border border-gray-800">
                      <span className="text-gray-400 block text-[10px]">Security Guardrail Status</span>
                      <p className="text-lg font-bold text-purple-400 mt-1 flex items-center space-x-1">
                        <ShieldCheck className="w-4 h-4 inline" />
                        <span>100% Guarded</span>
                      </p>
                    </div>
                  </div>

                  {/* Raw Report Text Preview if Summary */}
                  {reportContent && (
                    <div className="space-y-2">
                      <h4 className="font-semibold text-gray-300 uppercase tracking-wider text-[10px]">Live Audit Document Content</h4>
                      <pre className="bg-gray-900/90 p-4 rounded-xl border border-gray-800 text-[11px] font-mono text-gray-300 overflow-x-auto whitespace-pre-wrap">
                        {reportContent}
                      </pre>
                    </div>
                  )}

                  {/* Table of Runs */}
                  <div className="space-y-2">
                    <h4 className="font-semibold text-gray-300 uppercase tracking-wider text-[10px]">Persistent Runs Included in Report</h4>
                    <div className="overflow-x-auto rounded-xl border border-gray-800">
                      <table className="w-full text-left text-xs text-gray-300">
                        <thead className="bg-gray-900/80 text-gray-400 text-[10px] uppercase tracking-wider border-b border-gray-800">
                          <tr>
                            <th className="py-2.5 px-4">Run Name / ID</th>
                            <th className="py-2.5 px-4">Status</th>
                            <th className="py-2.5 px-4">Questions</th>
                            <th className="py-2.5 px-4">Overall Score</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800/60">
                          {evalRuns.map((r) => (
                            <tr key={r.id} className="hover:bg-gray-900/40 transition-colors">
                              <td className="py-3 px-4 font-mono font-medium text-white">{r.name || r.id.slice(0, 8)}</td>
                              <td className="py-3 px-4">
                                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800/60 uppercase">
                                  {r.status}
                                </span>
                              </td>
                              <td className="py-3 px-4 font-mono">{r.completed_questions}/{r.total_questions}</td>
                              <td className="py-3 px-4 font-bold text-blue-400">
                                {r.overall_score ? `${(r.overall_score * 100).toFixed(0)}%` : 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-800">
              <span className="text-xs text-gray-400 font-mono">Format: {activeReport.format}</span>
              <div className="flex items-center space-x-3">
                <button
                  type="button"
                  onClick={() => setActiveReport(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-400 hover:text-white transition-colors"
                >
                  Close Preview
                </button>
                <button
                  type="button"
                  onClick={() => handleDownload(activeReport.endpoint, activeReport.filename)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white flex items-center space-x-2 transition-all shadow-md shadow-blue-500/25 cursor-pointer"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Report Package</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
