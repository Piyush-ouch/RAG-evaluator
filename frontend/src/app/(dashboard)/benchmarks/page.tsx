'use client';

import React, { useState } from 'react';
import { FileSpreadsheet, Upload, Plus, Download, BookOpen, Layers, CheckCircle } from 'lucide-react';

interface SuiteItem {
  id: string;
  name: string;
  domain: string;
  questionsCount: number;
  isTemplate: boolean;
  version: string;
}

const initialSuites: SuiteItem[] = [
  { id: 'suite-101', name: 'General Knowledge QA', domain: 'General', questionsCount: 120, isTemplate: true, version: '1.0' },
  { id: 'suite-102', name: 'HIPAA & Medical Guidelines', domain: 'Healthcare', questionsCount: 85, isTemplate: true, version: '2.1' },
  { id: 'suite-103', name: 'Financial Regulations & Compliance', domain: 'Finance', questionsCount: 95, isTemplate: true, version: '1.4' },
  { id: 'suite-104', name: 'Contract Clauses Benchmark', domain: 'Legal', questionsCount: 64, isTemplate: true, version: '1.1' },
];

export default function BenchmarksPage() {
  const [suites, setSuites] = useState<SuiteItem[]>(initialSuites);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [suiteName, setSuiteName] = useState('');
  const [domain, setDomain] = useState('Custom');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Benchmark Suites & Datasets</h1>
          <p className="text-xs text-gray-400 mt-1">Manage standard domain benchmark datasets or upload custom CSV / JSON / Excel test banks.</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowUploadModal(true)}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 flex items-center space-x-2 transition-all"
          >
            <Upload className="w-4 h-4" />
            <span>Import Dataset (CSV/JSON)</span>
          </button>
          <button className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/25 flex items-center space-x-2 transition-all">
            <Plus className="w-4 h-4" />
            <span>Create Suite</span>
          </button>
        </div>
      </div>

      {/* Benchmark Suites Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {suites.map((suite) => (
          <div key={suite.id} className="glass-panel p-5 rounded-2xl border border-gray-800 hover:border-blue-500/40 transition-all flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-950/80 text-blue-400 border border-blue-800/60 uppercase tracking-wide">
                  {suite.domain}
                </span>
                <span className="text-[11px] font-mono text-gray-400">v{suite.version}</span>
              </div>
              <h3 className="text-base font-semibold text-white mt-3">{suite.name}</h3>
              <p className="text-xs text-gray-400 mt-1 flex items-center">
                <BookOpen className="w-3.5 h-3.5 mr-1.5 text-gray-500" />
                {suite.questionsCount} Evaluated Questions
              </p>
            </div>

            <div className="pt-4 border-t border-gray-800/80 flex items-center justify-between text-xs">
              <span className="text-gray-500 text-[11px]">{suite.isTemplate ? 'Built-in Template' : 'Custom Dataset'}</span>
              <button className="text-blue-400 hover:text-blue-300 font-medium flex items-center">
                Manage Questions &rarr;
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Dataset Import Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-md p-6 rounded-2xl border border-gray-800 bg-[#0f172a] space-y-5">
            <h2 className="text-lg font-bold text-white">Import Custom Test Bank</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Suite Name</label>
                <input
                  type="text"
                  placeholder="e.g. Legal Compliance Test 2026"
                  value={suiteName}
                  onChange={(e) => setSuiteName(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3.5 py-2 text-xs text-white outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Domain Category</label>
                <select
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-blue-500"
                >
                  <option value="Healthcare">Healthcare</option>
                  <option value="Finance">Finance</option>
                  <option value="Legal">Legal</option>
                  <option value="Insurance">Insurance</option>
                  <option value="Education">Education</option>
                  <option value="Government">Government</option>
                  <option value="Custom">Custom</option>
                </select>
              </div>

              {/* Upload Dropzone */}
              <div className="border-2 border-dashed border-gray-800 hover:border-blue-500/50 rounded-xl p-6 text-center cursor-pointer transition-colors bg-gray-900/40">
                <Upload className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                <p className="text-xs font-medium text-gray-200">Drag & drop CSV, JSON, or Excel dataset here</p>
                <p className="text-[10px] text-gray-500 mt-1">Columns required: question, expected_answer, category</p>
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-800">
              <button
                type="button"
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium bg-gray-800 text-gray-300 hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-500/20"
              >
                Upload & Process
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
