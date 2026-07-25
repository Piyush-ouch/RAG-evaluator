'use client';

import React from 'react';
import { BarChart3, TrendingUp, Cpu, Database, DollarSign, Activity } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const modelComparison = [
  { model: 'GPT-4o', accuracy: 96, hallucination: 1.2, cost: 0.045, latency: 890 },
  { model: 'Claude 3.5 Sonnet', accuracy: 95, hallucination: 1.8, cost: 0.038, latency: 940 },
  { model: 'Gemini 1.5 Pro', accuracy: 92, hallucination: 2.5, cost: 0.025, latency: 1020 },
  { model: 'Llama 3 70B (Groq)', accuracy: 89, hallucination: 3.8, cost: 0.008, latency: 420 },
];

const radarData = [
  { subject: 'Accuracy', A: 96, B: 89 },
  { subject: 'Faithfulness', A: 98, B: 85 },
  { subject: 'Retrieval', A: 94, B: 88 },
  { subject: 'Guardrails', A: 100, B: 96 },
  { subject: 'Citation', A: 95, B: 82 },
  { subject: 'Speed', A: 75, B: 98 },
];

export default function AnalyticsPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">System Performance & Model Leaderboard</h1>
        <p className="text-xs text-gray-400 mt-1">Cross-model benchmarks, cost-efficiency analysis, and multi-domain evaluation radar.</p>
      </div>

      {/* Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Accuracy vs Latency Bar Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-gray-800">
          <h2 className="text-base font-semibold text-white mb-1">Model Accuracy Comparison</h2>
          <p className="text-xs text-gray-400 mb-6">Percentage score across benchmark test suites</p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modelComparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="model" stroke="#6b7280" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px' }} />
                <Bar dataKey="accuracy" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Multi-Dimensional Radar Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-gray-800">
          <h2 className="text-base font-semibold text-white mb-1">Capabilities Radar</h2>
          <p className="text-xs text-gray-400 mb-6">GPT-4o (Blue) vs Llama 3 70B (Purple)</p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#1f2937" />
                <PolarAngleAxis dataKey="subject" stroke="#9ca3af" fontSize={11} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#4b5563" />
                <Radar name="GPT-4o" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.4} />
                <Radar name="Llama 3 70B" dataKey="B" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.4} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="glass-panel rounded-2xl border border-gray-800 overflow-hidden">
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-base font-semibold text-white">RAG Engine Leaderboard</h2>
          <p className="text-xs text-gray-400">Benchmark results aggregated from 5,000+ test queries</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-gray-900/60 text-gray-400 uppercase text-[10px] tracking-wider border-b border-gray-800">
              <tr>
                <th className="py-3.5 px-6">Model Architecture</th>
                <th className="py-3.5 px-6">Accuracy</th>
                <th className="py-3.5 px-6">Hallucination Rate</th>
                <th className="py-3.5 px-6">Avg Latency</th>
                <th className="py-3.5 px-6">Cost / 1K Queries</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {modelComparison.map((m) => (
                <tr key={m.model} className="hover:bg-gray-800/30 transition-colors">
                  <td className="py-4 px-6 font-semibold text-white">{m.model}</td>
                  <td className="py-4 px-6 font-bold text-blue-400">{m.accuracy}%</td>
                  <td className="py-4 px-6 text-emerald-400 font-medium">{m.hallucination}%</td>
                  <td className="py-4 px-6 font-mono text-amber-400">{m.latency} ms</td>
                  <td className="py-4 px-6 font-mono text-gray-300">${m.cost}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
