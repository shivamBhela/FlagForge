"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderGit2,
  Flag,
  Code2,
  Network,
  FlaskConical,
  Activity,
  ShieldAlert,
  AlertTriangle,
  Sparkles,
  Layers,
  Sliders,
  Settings,
  Flame,
} from "lucide-react";

const navigationItems = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Projects", href: "/projects", icon: FolderGit2 },
  { name: "Feature Flags", href: "/flags", icon: Flag },
  { name: "Code Scanner", href: "/scanner", icon: Code2 },
  { name: "Dependency Map", href: "/dependencies", icon: Network },
  { name: "Chaos Lab", href: "/chaos", icon: FlaskConical },
  { name: "Live Monitor", href: "/monitor", icon: Activity },
  { name: "Release Guardian", href: "/guardian", icon: ShieldAlert },
  { name: "Incidents", href: "/incidents", icon: AlertTriangle },
  { name: "Cleanup Studio", href: "/cleanup", icon: Sparkles },
  { name: "Integrations", href: "/integrations", icon: Layers },
  { name: "Policies", href: "/policies", icon: Sliders },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-16 md:w-64 bg-[#0c121e] border-r border-[#1e293b] flex flex-col shrink-0 h-screen sticky top-0 select-none">
      {/* Brand logo */}
      <div className="h-16 flex items-center justify-center md:justify-start gap-3 px-4 md:px-6 border-b border-[#1e293b]">
        <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
          <Flame className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <span className="hidden md:inline font-bold text-white tracking-wider text-base">FLAGFORGE</span>
          <span className="hidden md:inline ml-1.5 text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
            PRO
          </span>
        </div>
      </div>

      {/* Nav list */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              aria-label={item.name}
              title={item.name}
              className={`flex items-center justify-center md:justify-start gap-3 px-3 md:px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-blue-600/15 text-blue-400 border border-blue-500/20 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-[#151e2e]"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
              <span className="hidden md:inline">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* System Status Pill */}
      <div className="p-4 border-t border-[#1e293b] text-xs text-slate-400 flex items-center justify-center md:justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="hidden md:inline">Core Connected</span>
        </div>
        <span className="hidden md:inline text-[11px] font-mono text-slate-500">v1.0.0</span>
      </div>
    </aside>
  );
}
