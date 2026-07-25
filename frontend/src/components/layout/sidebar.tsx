'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FolderKanban,
  FileSpreadsheet,
  PlayCircle,
  BarChart3,
  ShieldAlert,
  FileCheck2,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import { clsx } from 'clsx';

const navItems = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Benchmarks', href: '/benchmarks', icon: FileSpreadsheet },
  { name: 'Evaluations', href: '/evaluations', icon: PlayCircle },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Reports', href: '/reports', icon: FileCheck2 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export const Sidebar = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 glass-panel border-r border-gray-800 flex flex-col h-screen fixed left-0 top-0 z-30">
      {/* App Branding */}
      <div className="p-6 border-b border-gray-800/60 flex items-center space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <ShieldCheck className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-sm text-white tracking-wide">RAG Evaluator</h1>
          <p className="text-[10px] text-blue-400 font-semibold tracking-wider uppercase">Enterprise Edition</p>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/10 text-white border-l-2 border-blue-500 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/40'
              )}
            >
              <Icon className={clsx('w-4 h-4', isActive ? 'text-blue-400' : 'text-gray-500')} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Plan Status Card */}
      <div className="p-4 border-t border-gray-800/60">
        <div className="p-3.5 rounded-xl bg-gradient-to-br from-blue-950/40 to-slate-900/60 border border-blue-900/40">
          <div className="flex items-center justify-between text-xs text-gray-300 font-semibold mb-1">
            <span>Enterprise Guardrails</span>
            <span className="text-emerald-400 bg-emerald-950/80 px-1.5 py-0.5 rounded border border-emerald-800/60 text-[10px]">Active</span>
          </div>
          <p className="text-[11px] text-gray-400 mb-2">Automated benchmarking enabled</p>
          <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-400 h-full w-[42%]" />
          </div>
        </div>
      </div>
    </aside>
  );
};
