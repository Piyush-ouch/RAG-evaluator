'use client';

import React from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  Zap,
  CheckCircle2,
  TrendingUp,
  Sparkles,
  ArrowUpRight,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const trendData = [
  { name: 'Mon', accuracy: 88, hallucination: 4, latency: 1200 },
  { name: 'Tue', accuracy: 92, hallucination: 3, latency: 1150 },
  { name: 'Wed', accuracy: 91, hallucination: 5, latency: 1300 },
  { name: 'Thu', accuracy: 94, hallucination: 2, latency: 1050 },
  { name: 'Fri', accuracy: 96, hallucination: 1, latency: 980 },
  { name: 'Sat', accuracy: 95, hallucination: 2, latency: 1010 },
  { name: 'Sun', accuracy: 97, hallucination: 1, latency: 940 },
];

const mockEvaluations = [
  { id: 'eval-892', project: 'Customer Support Chatbot v2.4', suite: 'Finance QA Suite', score: 94.8, hallucination: '1.2%', security: '100%', status: 'Completed', time: '10 mins ago' },
  { id: 'eval-891', project: 'Medical Assistant RAG', suite: 'Healthcare Safety Benchmark', score: 91.2, hallucination: '2.8%', security: '98%', status: 'Completed', time: '1 hour ago' },
  { id: 'eval-890', project: 'Legal Document Copilot', suite: 'Contract Analysis Suite', score: 88.5, hallucination: '4.1%', security: '95%', status: 'Running', time: 'In Progress' },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-6 rounded-2xl border border-blue-900/30 bg-gradient-to-r from-blue-950/40 via-slate-900/60 to-purple-950/30">
        <div>
          <div className="flex items-center space-x-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" />
            <span>AI Quality & Guardrail Evaluator</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Enterprise Sandbox Dashboard</h1>
          <p className="text-sm text-gray-400 mt-1">Real-time benchmarks across accuracy, hallucination, latency, and prompt injection defense.</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="px-4 py-2 rounded-xl text-xs font-medium bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 transition-all">
            Export Audit Report
          </button>
          <button className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/25 transition-all">
            + Run Benchmark Suite
          </button>
        </div>
      </div>

      {/* KPI Scorecard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Overall Score */}
        <div className="glass-panel p-5 rounded-xl border border-gray-800 hover:border-blue-500/40 transition-all group">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400">Overall RAG Score</span>
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-white">94.8<span className="text-lg font-normal text-gray-400">/100</span></span>
            <span className="text-xs text-emerald-400 flex items-center font-medium">
              <TrendingUp className="w-3.5 h-3.5 mr-1" /> +2.4%
            </span>
          </div>
          <div className="mt-3 w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full w-[94.8%]" />
          </div>
        </div>

        {/* Hallucination Rate */}
        <div className="glass-panel p-5 rounded-xl border border-gray-800 hover:border-emerald-500/40 transition-all group">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400">Hallucination Rate</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-white">1.8%</span>
            <span className="text-xs text-emerald-400 font-medium">Low Risk</span>
          </div>
          <p className="text-[11px] text-gray-400 mt-2">Groundedness score: 98.2%</p>
        </div>

        {/* P95 Latency */}
        <div className="glass-panel p-5 rounded-xl border border-gray-800 hover:border-amber-500/40 transition-all group">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400">P95 Latency</span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-white">940<span className="text-sm font-normal text-gray-400"> ms</span></span>
            <span className="text-xs text-amber-400 font-medium">-85ms vs baseline</span>
          </div>
          <p className="text-[11px] text-gray-400 mt-2">TTFB: 320ms | Generation: 620ms</p>
        </div>

        {/* Security & Guardrail Score */}
        <div className="glass-panel p-5 rounded-xl border border-gray-800 hover:border-purple-500/40 transition-all group">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400">Guardrail Defense</span>
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-white">99.1%</span>
            <span className="text-xs text-emerald-400 font-medium">0 Jailbreaks</span>
          </div>
          <p className="text-[11px] text-gray-400 mt-2">Passed 450 adversarial vectors</p>
        </div>
      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Analysis Chart */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-gray-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-semibold text-white">Accuracy & Hallucination Trends</h2>
              <p className="text-xs text-gray-400">7-day continuous benchmark monitoring</p>
            </div>
            <div className="flex items-center space-x-4 text-xs">
              <span className="flex items-center text-gray-300">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500 mr-2" /> Accuracy
              </span>
              <span className="flex items-center text-gray-300">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 mr-2" /> Hallucination Rate
              </span>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', color: '#fff' }}
                />
                <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="hallucination" stroke="#f43f5e" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Guardrail Breakdown */}
        <div className="glass-panel p-6 rounded-2xl border border-gray-800 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold text-white mb-1">Guardrail Vulnerability Map</h2>
            <p className="text-xs text-gray-400 mb-6">Adversarial test pass rates</p>

            <div className="space-y-4">
              {[
                { label: 'Prompt Injection', score: 100, color: 'bg-emerald-500' },
                { label: 'Jailbreak Resistance', score: 98, color: 'bg-blue-500' },
                { label: 'PII Leakage Prevention', score: 100, color: 'bg-emerald-500' },
                { label: 'System Prompt Extraction', score: 96, color: 'bg-indigo-500' },
                { label: 'Toxicity & Harm Defense', score: 100, color: 'bg-emerald-500' },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-gray-300 font-medium">{item.label}</span>
                    <span className="text-gray-200 font-bold">{item.score}%</span>
                  </div>
                  <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                    <div className={`${item.color} h-full rounded-full`} style={{ width: `${item.score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-800/80 flex items-center justify-between text-xs">
            <span className="text-gray-400">Total Security Checks</span>
            <span className="font-mono text-blue-400 font-semibold">1,240 Prompt Vectors</span>
          </div>
        </div>
      </div>

      {/* Recent Evaluations Table */}
      <div className="glass-panel rounded-2xl border border-gray-800 overflow-hidden">
        <div className="p-6 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Recent Benchmark Executions</h2>
            <p className="text-xs text-gray-400">Automated evaluation runs across configured project pipelines</p>
          </div>
          <button className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center">
            View All Runs <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-gray-900/60 text-gray-400 uppercase text-[10px] tracking-wider border-b border-gray-800">
              <tr>
                <th className="py-3.5 px-6">Evaluation Run</th>
                <th className="py-3.5 px-6">Project</th>
                <th className="py-3.5 px-6">Benchmark Suite</th>
                <th className="py-3.5 px-6">Overall Score</th>
                <th className="py-3.5 px-6">Hallucination</th>
                <th className="py-3.5 px-6">Security Defense</th>
                <th className="py-3.5 px-6">Status</th>
                <th className="py-3.5 px-6">Completed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {mockEvaluations.map((item) => (
                <tr key={item.id} className="hover:bg-gray-800/30 transition-colors">
                  <td className="py-4 px-6 font-mono text-blue-400 font-medium">{item.id}</td>
                  <td className="py-4 px-6 font-medium text-white">{item.project}</td>
                  <td className="py-4 px-6 text-gray-300">{item.suite}</td>
                  <td className="py-4 px-6">
                    <span className="font-bold text-emerald-400">{item.score}</span>
                    <span className="text-gray-500">/100</span>
                  </td>
                  <td className="py-4 px-6 text-gray-300">{item.hallucination}</td>
                  <td className="py-4 px-6 text-gray-300">{item.security}</td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                      item.status === 'Completed' ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60' : 'bg-blue-950/80 text-blue-400 border border-blue-800/60'
                    }`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-gray-400">{item.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
