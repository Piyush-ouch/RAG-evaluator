'use client';

import React from 'react';
import { FileCheck2, Download, FileText, ShieldAlert, Award, FileSpreadsheet, Sparkles } from 'lucide-react';

const reports = [
  { id: 'rep-01', title: 'Executive Summary & RAG Health Index', type: 'Executive Summary', date: 'July 25, 2026', size: '2.4 MB', format: 'PDF' },
  { id: 'rep-02', title: 'AI Safety & Adversarial Security Audit', type: 'Security Audit', date: 'July 24, 2026', size: '1.8 MB', format: 'PDF' },
  { id: 'rep-03', title: 'Hallucination & Retrieval Groundedness Log', type: 'Hallucination Report', date: 'July 23, 2026', size: '4.1 MB', format: 'CSV' },
  { id: 'rep-04', title: 'Token Usage & Cost Analysis', type: 'Cost Report', date: 'July 22, 2026', size: '850 KB', format: 'JSON' },
];

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Enterprise Audit Reports</h1>
          <p className="text-xs text-gray-400 mt-1">Export compliance-ready PDF, CSV, and JSON reports with automated safety recommendations.</p>
        </div>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reports.map((rep) => (
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
                  <p className="text-xs text-gray-400 mt-0.5">Generated: {rep.date} &bull; {rep.size}</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-gray-900 text-gray-300 border border-gray-800">
                {rep.format}
              </span>
            </div>

            <div className="pt-4 border-t border-gray-800/80 flex items-center justify-between">
              <span className="text-xs text-gray-500 font-mono">{rep.id}</span>
              <button className="px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white flex items-center space-x-2 transition-all shadow-md shadow-blue-500/20">
                <Download className="w-3.5 h-3.5" />
                <span>Download Report</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
