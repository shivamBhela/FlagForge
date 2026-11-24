import React from "react";
import { Bell, Search, ShieldCheck } from "lucide-react";

export function Header() {
  return (
    <header className="h-16 border-b border-[#1e293b] bg-[#0c121e]/80 backdrop-blur px-8 flex items-center justify-between shrink-0 sticky top-0 z-20">
      {/* Search Bar */}
      <div className="flex items-center gap-3 w-96">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search flags, environments, repositories, or graph nodes..."
            className="w-full bg-[#151e2e] border border-[#1e293b] rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/60 transition-colors"
          />
        </div>
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-4">
        {/* Flagsmith Status Indicator */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Flagsmith Synced</span>
        </div>

        {/* Notifications */}
        <button
          className="w-8 h-8 rounded-lg bg-[#151e2e] border border-[#1e293b] flex items-center justify-center text-slate-400 hover:text-slate-200 hover:border-slate-700 transition"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
        </button>

        {/* User avatar / org badge */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-[#1e293b]">
          <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-semibold text-white">
            FF
          </div>
          <div className="text-left text-xs leading-tight">
            <p className="font-medium text-slate-200">Engineering Org</p>
            <p className="text-[10px] text-slate-400">Production Guard</p>
          </div>
        </div>
      </div>
    </header>
  );
}
