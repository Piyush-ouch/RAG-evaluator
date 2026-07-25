'use client';

import React from 'react';
import Link from 'next/link';
import { ShieldCheck, PlayCircle, Bot, Zap, Lock, ChevronRight, BarChart3, Sparkles, CheckCircle } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0b0f17] text-gray-100 flex flex-col justify-between selection:bg-blue-600 selection:text-white">
      {/* Navbar */}
      <header className="border-b border-gray-800/80 glass-panel sticky top-0 z-40 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-base text-white tracking-tight">RAG Evaluator</span>
            <span className="ml-2 text-[10px] bg-blue-950/80 text-blue-400 border border-blue-800/60 px-1.5 py-0.5 rounded font-mono font-semibold uppercase">Enterprise</span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <Link href="/login" className="text-xs font-semibold text-gray-300 hover:text-white px-3 py-2 transition-colors">
            Sign In
          </Link>
          <Link href="/register" className="text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-4 py-2 rounded-xl shadow-lg shadow-blue-500/25 transition-all">
            Get Started &rarr;
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-6xl mx-auto px-6 py-20 text-center flex flex-col items-center justify-center space-y-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-950/60 border border-blue-800/60 text-xs font-medium text-blue-400">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Automated RAG Benchmarking & Guardrail Evaluator</span>
        </div>

        <h1 className="text-5xl md:text-6xl font-extrabold text-white tracking-tight leading-tight max-w-4xl">
          Evaluate, Benchmark, and Secure Your <span className="gradient-text">Enterprise RAG Systems</span>
        </h1>

        <p className="text-base text-gray-400 max-w-2xl leading-relaxed">
          Connect your AI chatbot API. Automatically execute thousands of benchmark questions across hallucination, context precision, faithfulness, latency, token cost, prompt injection, and PII leakage.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            href="/dashboard"
            className="w-full sm:w-auto px-8 py-3.5 rounded-2xl text-sm font-semibold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-xl shadow-blue-500/25 flex items-center justify-center space-x-2 transition-all"
          >
            <span>Open Sandbox Dashboard</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
          <Link
            href="/login"
            className="w-full sm:w-auto px-8 py-3.5 rounded-2xl text-sm font-medium bg-gray-900 hover:bg-gray-800 text-gray-200 border border-gray-800 transition-all"
          >
            Sign In to Platform
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left w-full pt-16">
          <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">18 AI Quality Evaluators</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Measure hallucination rates, token-level F1 correctness, faithfulness, and chunk relevance with precision.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <Lock className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">Adversarial Guardrail Defense</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Test prompt injection, DAN jailbreaks, PII leakage, SQL injection, and system prompt extraction resistance.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">Async Celery Worker Scalability</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Execute thousands of benchmark queries asynchronously backed by PostgreSQL, Redis, and MinIO / AWS S3.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800/60 py-6 text-center text-xs text-gray-500">
        <p>&copy; 2026 Enterprise RAG Sandbox & Guardrail Evaluator. Production-Grade SaaS Platform.</p>
      </footer>
    </div>
  );
}
