'use client';

import React, { useState } from 'react';
import { Plus, Bot, Database, Cpu, Globe, CheckCircle2, Shield, Settings2, RefreshCw } from 'lucide-react';

interface ProjectItem {
  id: string;
  name: string;
  url: string;
  llm: string;
  vectorDb: string;
  evalCount: number;
  lastTested: string;
}

const initialProjects: ProjectItem[] = [
  {
    id: 'proj-001',
    name: 'Customer Support AI Assistant',
    url: 'https://api.chatbot.internal/v1/chat',
    llm: 'OpenAI (GPT-4o)',
    vectorDb: 'Pinecone (Index: kb-prod)',
    evalCount: 42,
    lastTested: '10 mins ago',
  },
  {
    id: 'proj-002',
    name: 'Financial Advisory Copilot',
    url: 'https://fin.ai.internal/v1/query',
    llm: 'Anthropic (Claude 3.5 Sonnet)',
    vectorDb: 'Qdrant (Collection: fin_docs)',
    evalCount: 18,
    lastTested: '2 hours ago',
  },
];

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectItem[]>(initialProjects);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [llm, setLlm] = useState('openai');
  const [vectorDb, setVectorDb] = useState('qdrant');

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !url) return;
    const newProj: ProjectItem = {
      id: `proj-00${projects.length + 1}`,
      name,
      url,
      llm: llm === 'openai' ? 'OpenAI (GPT-4o)' : llm === 'anthropic' ? 'Anthropic (Claude 3.5)' : 'Ollama (Local)',
      vectorDb: vectorDb === 'pinecone' ? 'Pinecone (prod)' : vectorDb === 'qdrant' ? 'Qdrant (v1)' : 'Chroma (local)',
      evalCount: 0,
      lastTested: 'Just created',
    };
    setProjects([newProj, ...projects]);
    setShowModal(false);
    setName('');
    setUrl('');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">RAG Projects & Integrations</h1>
          <p className="text-xs text-gray-400 mt-1">Connect AI chatbot APIs, LLM judges, and vector databases for automated benchmarking.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/25 flex items-center space-x-2 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Connect New Project</span>
        </button>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {projects.map((proj) => (
          <div key={proj.id} className="glass-panel p-6 rounded-2xl border border-gray-800 hover:border-blue-500/40 transition-all flex flex-col justify-between space-y-5">
            <div>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">{proj.name}</h3>
                    <p className="text-xs font-mono text-gray-400 flex items-center mt-0.5">
                      <Globe className="w-3 h-3 mr-1 text-gray-500" /> {proj.url}
                    </p>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">Active</span>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3 pt-4 border-t border-gray-800/80 text-xs">
                <div className="p-3 rounded-lg bg-gray-900/60 border border-gray-800">
                  <span className="text-gray-500 font-medium flex items-center mb-1">
                    <Cpu className="w-3.5 h-3.5 mr-1.5 text-blue-400" /> LLM Provider
                  </span>
                  <p className="font-medium text-gray-200">{proj.llm}</p>
                </div>
                <div className="p-3 rounded-lg bg-gray-900/60 border border-gray-800">
                  <span className="text-gray-500 font-medium flex items-center mb-1">
                    <Database className="w-3.5 h-3.5 mr-1.5 text-purple-400" /> Vector Database
                  </span>
                  <p className="font-medium text-gray-200">{proj.vectorDb}</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-gray-800/60 text-xs">
              <span className="text-gray-400">Total Evaluations: <strong className="text-white">{proj.evalCount}</strong></span>
              <div className="flex items-center space-x-2">
                <button className="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 font-medium flex items-center space-x-1">
                  <RefreshCw className="w-3 h-3 mr-1 text-gray-400" /> Test Connection
                </button>
                <button className="px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 font-medium">
                  Settings
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal for creating a new project */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-lg p-6 rounded-2xl border border-gray-800 bg-[#0f172a] space-y-5">
            <h2 className="text-lg font-bold text-white">Connect AI Chatbot API</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Legal AI Assistant"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3.5 py-2 text-xs text-white outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Chatbot API Endpoint URL</label>
                <input
                  type="url"
                  required
                  placeholder="https://api.yourcompany.com/v1/chat"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3.5 py-2 text-xs text-white outline-none focus:border-blue-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">LLM Provider</label>
                  <select
                    value={llm}
                    onChange={(e) => setLlm(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-blue-500"
                  >
                    <option value="openai">OpenAI (GPT-4o)</option>
                    <option value="anthropic">Anthropic (Claude 3.5)</option>
                    <option value="gemini">Google Gemini Pro</option>
                    <option value="groq">Groq (Llama 3)</option>
                    <option value="deepseek">DeepSeek V3</option>
                    <option value="ollama">Ollama (Local)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">Vector DB</label>
                  <select
                    value={vectorDb}
                    onChange={(e) => setVectorDb(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-blue-500"
                  >
                    <option value="pinecone">Pinecone</option>
                    <option value="qdrant">Qdrant</option>
                    <option value="weaviate">Weaviate</option>
                    <option value="milvus">Milvus</option>
                    <option value="chroma">Chroma</option>
                    <option value="faiss">FAISS</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium bg-gray-800 text-gray-300 hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-500/20"
                >
                  Save Configuration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
