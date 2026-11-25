'use client';

import React, { useState } from 'react';
import { Settings, CreditCard, Key, Shield, Building, UserCheck, ExternalLink, Check, Copy, Bot, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'providers' | 'org' | 'api' | 'billing'>('providers');
  const [copied, setCopied] = useState(false);

  // Gemini API Key state
  const [geminiKey, setGeminiKey] = useState('');
  const [testingGemini, setTestingGemini] = useState(false);
  const [geminiStatus, setGeminiStatus] = useState<{ success: boolean; message: str; model?: str } | null>(null);

  const handleCopyKey = () => {
    navigator.clipboard.writeText('rge_live_892348a9f8e7123c89a0b');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTestGemini = async () => {
    setTestingGemini(true);
    setGeminiStatus(null);

    const activeModels = ['gemini-3.5-flash-lite', 'gemma-4-26b-a4b-it', 'gemma-4-31b-it', 'gemini-3.8-flash'];

    try {
      // If user left input empty, test the backend's configured GOOGLE_AI_API_KEY via /api/v1/demo/chatbot
      if (!geminiKey.trim()) {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        const res = await fetch(`${apiBase}/demo/chatbot`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: 'Confirm that the live Google Gemini API integration is active and working in one sentence.',
          }),
        });
        const data = await res.json();
        if (res.ok && data.answer) {
          setGeminiStatus({
            success: true,
            message: `Backend .env Key Connected! Response: "${data.answer}" (${data.latency_ms}ms)`,
            model: data.model || 'gemini-3.5-flash-lite',
          });
        } else {
          setGeminiStatus({
            success: false,
            message: 'Backend Gemini test failed. Please paste a valid Gemini API key above.',
          });
        }
        return;
      }

      // Test pasted key directly against active Gemini / Gemma models
      let lastError = 'Invalid Gemini API key or quota exceeded.';
      for (const modelName of activeModels) {
        const res = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${geminiKey.trim()}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              contents: [{ parts: [{ text: "Respond with: 'Gemini API is connected successfully!'" }] }],
            }),
          }
        );

        const data = await res.json();

        if (res.ok && data.candidates && data.candidates.length > 0) {
          const parts = data.candidates[0]?.content?.parts || [];
          const nonThought = parts.filter((p: any) => !p.thought).map((p: any) => p.text || '').join('');
          const text = nonThought || parts.map((p: any) => p.text || '').join('');
          setGeminiStatus({
            success: true,
            message: `Connection Successful! Gemini Response: "${text.trim()}"`,
            model: modelName,
          });
          return;
        } else if (data.error?.message) {
          lastError = data.error.message;
        }
      }

      setGeminiStatus({
        success: false,
        message: lastError,
      });
    } catch (err: any) {
      setGeminiStatus({
        success: false,
        message: err.message || 'Failed to connect to Gemini API.',
      });
    } finally {
      setTestingGemini(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Organization Settings & AI Providers</h1>
        <p className="text-xs text-gray-400 mt-1">Manage AI model keys, vector DB configurations, team roles, and billing.</p>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-gray-800 pb-3 overflow-x-auto">
        {[
          { id: 'providers', label: 'AI Model Providers & Keys', icon: Bot },
          { id: 'billing', label: 'Stripe Billing & Plans', icon: CreditCard },
          { id: 'api', label: 'Platform API Keys', icon: Key },
          { id: 'org', label: 'Organization & Team', icon: Building },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/40'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* AI Providers Tab */}
      {activeTab === 'providers' && (
        <div className="space-y-6">
          {/* Google Gemini Card */}
          <div className="glass-panel p-6 rounded-2xl border border-blue-900/40 bg-slate-900/60 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white font-bold shadow-md">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Google Gemini Provider</h3>
                  <p className="text-xs text-gray-400">Google AI Studio API (gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash)</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Supported Adapter
              </span>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-gray-300">Gemini API Key</label>
              <div className="flex items-center space-x-3">
                <input
                  type="password"
                  placeholder="Paste your Gemini API key (AIzaSy...)"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-gray-950 border border-gray-800 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleTestGemini}
                  disabled={testingGemini}
                  className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center space-x-2 transition-all shadow-md shadow-blue-500/20 disabled:opacity-50"
                >
                  {testingGemini ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                  <span>{testingGemini ? 'Testing Key...' : 'Test Key on Web'}</span>
                </button>
              </div>
            </div>

            {/* Test Connection Status Banner */}
            {geminiStatus && (
              <div className={`p-4 rounded-xl text-xs flex items-start space-x-3 border ${
                geminiStatus.success
                  ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
                  : 'bg-rose-950/40 border-rose-800/60 text-rose-300'
              }`}>
                {geminiStatus.success ? (
                  <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <p className="font-semibold">{geminiStatus.message}</p>
                  {geminiStatus.model && (
                    <p className="text-[11px] opacity-80 mt-0.5">Model Tested: {geminiStatus.model}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Billing Tab Content */}
      {activeTab === 'billing' && (
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-blue-900/40 bg-gradient-to-r from-blue-950/40 via-slate-900/60 to-purple-950/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30 uppercase tracking-wide">
                Current Plan
              </span>
              <h2 className="text-xl font-bold text-white mt-1">Enterprise Subscription</h2>
              <p className="text-xs text-gray-400 mt-0.5">Unlimited automated benchmark runs, full AI guardrail evaluation, custom SLA & priority workers.</p>
            </div>
            <button className="px-4 py-2 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-white border border-gray-700 flex items-center space-x-2 transition-all">
              <span>Stripe Customer Portal</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* API Keys Content */}
      {activeTab === 'api' && (
        <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-4">
          <h3 className="text-base font-semibold text-white">Platform API Keys</h3>
          <p className="text-xs text-gray-400">Use these keys to trigger benchmark runs programmatically from CI/CD pipelines.</p>

          <div className="p-4 rounded-xl bg-gray-900 border border-gray-800 flex items-center justify-between font-mono text-xs">
            <span className="text-gray-300">rge_live_892348a9f8e7123c89a0b****************</span>
            <button
              onClick={handleCopyKey}
              className="px-3 py-1.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-200 flex items-center space-x-1.5 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Key'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
