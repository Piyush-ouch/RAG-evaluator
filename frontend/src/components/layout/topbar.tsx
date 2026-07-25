'use client';

import React from 'react';
import { useAuth } from '@/lib/auth-context';
import { Bell, Search, User as UserIcon, LogOut, ChevronDown, Command } from 'lucide-react';

export const Topbar = () => {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 glass-panel border-b border-gray-800 fixed top-0 right-0 left-64 z-20 px-6 flex items-center justify-between">
      {/* Search / Command Bar */}
      <div className="flex items-center space-x-3 w-96 bg-gray-900/60 border border-gray-800 rounded-lg px-3.5 py-1.5 text-xs text-gray-400 focus-within:border-blue-500 transition-colors">
        <Search className="w-3.5 h-3.5 text-gray-500" />
        <input
          type="text"
          placeholder="Search evaluations, benchmarks, projects... (⌘K)"
          className="bg-transparent border-none outline-none text-white w-full placeholder-gray-500"
        />
        <kbd className="bg-gray-800 text-[10px] px-1.5 py-0.5 rounded text-gray-400 font-mono">⌘K</kbd>
      </div>

      {/* Right controls */}
      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <button className="relative p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800/60 transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-500 rounded-full" />
        </button>

        {/* User profile dropdown */}
        <div className="flex items-center space-x-3 border-l border-gray-800 pl-4">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-600 flex items-center justify-center text-white font-semibold text-xs border border-white/10 shadow-sm">
            {user ? `${user.first_name[0]}${user.last_name[0]}` : 'U'}
          </div>
          <div className="text-left hidden md:block">
            <p className="text-xs font-semibold text-white leading-tight">{user ? `${user.first_name} ${user.last_name}` : 'Enterprise User'}</p>
            <p className="text-[10px] text-gray-400 capitalize">{user?.role || 'Admin'}</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 text-gray-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition-colors ml-2"
            title="Log out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
