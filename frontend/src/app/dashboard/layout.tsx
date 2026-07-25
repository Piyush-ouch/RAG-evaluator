'use client';

import React from 'react';
import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#0b0f17] flex">
      <Sidebar />
      <div className="flex-1 flex flex-col pl-64">
        <Topbar />
        <main className="flex-1 pt-20 px-8 pb-12 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
