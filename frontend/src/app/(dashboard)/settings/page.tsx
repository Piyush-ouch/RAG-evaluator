'use client';

import React, { useState } from 'react';
import { Settings, CreditCard, Key, Shield, Building, UserCheck, ExternalLink, Check, Copy } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'org' | 'api' | 'billing'>('billing');
  const [copied, setCopied] = useState(false);

  const handleCopyKey = () => {
    navigator.clipboard.writeText('rge_live_892348a9f8e7123c89a0b');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Organization Settings & Billing</h1>
        <p className="text-xs text-gray-400 mt-1">Manage tenant configuration, team roles, API keys, and Stripe subscription.</p>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-gray-800 pb-3">
        {[
          { id: 'billing', label: 'Stripe Billing & Plans', icon: CreditCard },
          { id: 'api', label: 'API Keys', icon: Key },
          { id: 'org', label: 'Organization & Team', icon: Building },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all ${
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

      {/* Billing Tab Content */}
      {activeTab === 'billing' && (
        <div className="space-y-6">
          {/* Current Active Subscription Banner */}
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

          {/* Pricing Tiers */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Free Tier */}
            <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-5">
              <div>
                <h3 className="text-lg font-bold text-white">Free Sandbox</h3>
                <p className="text-xs text-gray-400 mt-1">For testing & initial validation</p>
                <div className="mt-4">
                  <span className="text-3xl font-extrabold text-white">$0</span>
                  <span className="text-xs text-gray-500"> / month</span>
                </div>
              </div>
              <ul className="space-y-2.5 text-xs text-gray-300">
                <li className="flex items-center"><Check className="w-4 h-4 text-emerald-400 mr-2" /> 100 benchmark queries / mo</li>
                <li className="flex items-center"><Check className="w-4 h-4 text-emerald-400 mr-2" /> Basic quality evaluators</li>
                <li className="flex items-center"><Check className="w-4 h-4 text-emerald-400 mr-2" /> Standard PDF export</li>
              </ul>
              <button className="w-full py-2 rounded-xl text-xs font-semibold bg-gray-800 text-gray-400 cursor-not-allowed">
                Included
              </button>
            </div>

            {/* Pro Tier */}
            <div className="glass-panel p-6 rounded-2xl border border-blue-800/60 bg-gradient-to-b from-blue-950/20 to-slate-900/40 space-y-5 relative">
              <div>
                <h3 className="text-lg font-bold text-white">Pro Evaluator</h3>
                <p className="text-xs text-gray-400 mt-1">For growing AI engineering teams</p>
                <div className="mt-4">
                  <span className="text-3xl font-extrabold text-white">$299</span>
                  <span className="text-xs text-gray-500"> / month</span>
                </div>
              </div>
              <ul className="space-y-2.5 text-xs text-gray-300">
                <li className="flex items-center"><Check className="w-4 h-4 text-blue-400 mr-2" /> 5,000 queries / mo</li>
                <li className="flex items-center"><Check className="w-4 h-4 text-blue-400 mr-2" /> All 18 AI evaluators</li>
                <li className="flex items-center"><Check className="w-4 h-4 text-blue-400 mr-2" /> Celery background workers</li>
                <li className="flex items-center"><Check className="w-4 h-4 text-blue-400 mr-2" /> Version regression history</li>
              </ul>
              <button className="w-full py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-500/20 transition-all">
                Upgrade with Stripe Checkout
              </button>
            </div>

            {/* Enterprise Tier */}
            <div className="glass-panel p-6 rounded-2xl border border-purple-800/60 bg-gradient-to-b from-purple-950/20 to-slate-900/40 space-y-5 relative">
              <span className="absolute -top-3 right-6 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider shadow-md">
                Active Plan
              </span>
              <div>
                <h3 className="text-lg font-bold text-white">Enterprise Scale</h3>
                <p className="text-xs text-gray-400 mt-1">Dedicated infrastructure & custom SLAs</p>
                <div className="mt-4">
                  <span className="text-3xl font-extrabold text-white">$999</span>
                  <span className="text-xs text-gray-500"> / month</span>
                </div>
              </div>
              <ul className="space-y-2.5 text-xs text-gray-300">
                <li className="flex items-center"><Check className="w-4 h-4 text-purple-400 mr-2" /> Unlimited queries</li>
                <li className="flex items-center"><Check className="w-4 h-4 text-purple-400 mr-2" /> Real-time guardrail defense</li>
                <li className="flex items-center"><Check className="w-4 h-4 text-purple-400 mr-2" /> Dedicated Celery queue</li>
                <li className="flex items-center"><Check className="w-4 h-4 text-purple-400 mr-2" /> AWS EKS / Custom K8s deployment</li>
              </ul>
              <button className="w-full py-2 rounded-xl text-xs font-semibold bg-purple-600 text-white cursor-default">
                Active Plan
              </button>
            </div>
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
