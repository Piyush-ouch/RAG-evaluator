'use client';

import React, { useState, useEffect } from 'react';
import { Upload, Plus, BookOpen, Sparkles, RefreshCw, Layers, CheckCircle2, ArrowRight } from 'lucide-react';
import Link from 'next/link';

interface SuiteItem {
  id: string;
  name: string;
  domain: string;
  question_count: number;
  is_template: boolean;
  version: string;
  source_dataset?: string | null;
  source_subset?: string | null;
  description?: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function BenchmarksPage() {
  const [suites, setSuites] = useState<SuiteItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isImporting, setIsImporting] = useState(false);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [suiteName, setSuiteName] = useState('');
  const [domain, setDomain] = useState('Custom');

  const fetchSuites = async () => {
    try {
      setIsLoading(true);
      const res = await fetch(`${API_BASE}/benchmarks/`);
      if (res.ok) {
        const data = await res.json();
        setSuites(data);
      }
    } catch (err) {
      console.warn('Failed to load benchmark suites from backend:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSuites();
  }, []);

  const handleSyncRAGBench = async () => {
    try {
      setIsImporting(true);
      setImportStatus('Importing 5 RAGBench subsets (FinQA, TAT-QA, PubMedQA, TechQA, HotpotQA)...');
      const res = await fetch(`${API_BASE}/benchmarks/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset: 'ragbench',
          subsets: ['finqa', 'tatqa', 'pubmedqa', 'techqa', 'hotpotqa'],
          split: 'test',
          limit_per_subset: 40,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setImportStatus(`Successfully synced! Inserted: ${data.total_inserted}, Duplicates skipped: ${data.total_duplicates}`);
        await fetchSuites();
        setTimeout(() => setImportStatus(null), 4000);
      } else {
        setImportStatus('Import failed. Check server logs.');
      }
    } catch (err) {
      setImportStatus('Error connecting to backend API.');
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Benchmark Suites & Datasets</h1>
          <p className="text-xs text-gray-400 mt-1">
            Standard domain benchmark datasets, RAGBench integration (FinQA, TAT-QA, PubMedQA, TechQA, HotpotQA), and custom test banks.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleSyncRAGBench}
            disabled={isImporting}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white flex items-center space-x-2 transition-all shadow-lg shadow-purple-500/20 cursor-pointer disabled:opacity-50"
          >
            {isImporting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>Sync RAGBench (200 Qs)</span>
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 flex items-center space-x-2 transition-all cursor-pointer"
          >
            <Upload className="w-4 h-4" />
            <span>Import Dataset</span>
          </button>
        </div>
      </div>

      {importStatus && (
        <div className="p-3 bg-indigo-950/60 border border-indigo-800/80 rounded-xl text-xs text-indigo-300 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-indigo-400" />
          <span>{importStatus}</span>
        </div>
      )}

      {/* Benchmark Suites Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center p-12 text-xs text-gray-400">
          <RefreshCw className="w-5 h-5 animate-spin mr-2 text-blue-500" />
          Loading benchmark suites from PostgreSQL...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {suites.map((suite) => (
            <div
              key={suite.id}
              className="glass-panel p-5 rounded-2xl border border-gray-800 hover:border-blue-500/40 transition-all flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-950/80 text-blue-400 border border-blue-800/60 uppercase tracking-wide">
                    {suite.domain}
                  </span>
                  <span className="text-[11px] font-mono text-gray-400">v{suite.version}</span>
                </div>
                <h3 className="text-base font-semibold text-white mt-3">{suite.name}</h3>
                {suite.description && (
                  <p className="text-xs text-gray-400 mt-1 line-clamp-2">{suite.description}</p>
                )}
                <div className="mt-3 flex items-center space-x-3 text-xs text-gray-400">
                  <span className="flex items-center">
                    <BookOpen className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
                    <strong>{suite.question_count}</strong>&nbsp;Questions
                  </span>
                  <span className="text-gray-600">•</span>
                  <span className="text-gray-400">
                    Source: <span className="text-gray-300 font-medium">{suite.source_dataset ? `RAGBench (${suite.source_subset})` : suite.is_template ? 'Template' : 'Custom'}</span>
                  </span>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-800/80 flex items-center justify-between text-xs">
                <span className="text-gray-500 text-[11px]">
                  {suite.source_dataset ? 'Canonical Benchmark' : suite.is_template ? 'Built-in Template' : 'Custom Bank'}
                </span>
                <Link
                  href={`/evaluations`}
                  className="text-blue-400 hover:text-blue-300 font-medium flex items-center space-x-1"
                >
                  <span>Evaluate Suite</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

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
                  <option value="Technical">Technical</option>
                  <option value="General">General</option>
                  <option value="Custom">Custom</option>
                </select>
              </div>

              <div className="border-2 border-dashed border-gray-800 hover:border-blue-500/50 rounded-xl p-6 text-center cursor-pointer transition-colors bg-gray-900/40">
                <Upload className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                <p className="text-xs font-medium text-gray-200">Drag & drop CSV, JSON, or Excel dataset here</p>
                <p className="text-[10px] text-gray-500 mt-1">Columns: question, expected_answer, category</p>
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-800">
              <button
                type="button"
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium bg-gray-800 text-gray-300 hover:bg-gray-700 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-500/20 cursor-pointer"
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
