"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Search, ShieldCheck, Building2, ChevronDown, Plus, LogOut, LogIn } from "lucide-react";

export function Header() {
  const { user, organizations, currentOrg, setCurrentOrg, logout } = useAuth();

  return (
    <header className="h-16 border-b border-[#1e293b] bg-[#0c121e]/80 backdrop-blur px-4 md:px-8 flex items-center justify-between shrink-0 sticky top-0 z-20">
      {/* Search Bar & Org Selector */}
      <div className="flex items-center gap-2 md:gap-4">
        {/* Organization Switcher Dropdown */}
        {user && (
          <div className="relative group">
            <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-xs text-slate-200 hover:border-slate-600 transition">
              <Building2 className="w-3.5 h-3.5 text-blue-400" />
              <span className="font-semibold max-w-[120px] truncate">
                {currentOrg ? currentOrg.name : "Select Org"}
              </span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {/* Dropdown Menu */}
            <div className="absolute left-0 top-full mt-1.5 w-52 py-1.5 bg-[#0c121e] border border-[#1e293b] rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 z-50">
              <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                Switch Organization
              </div>
              {organizations.map((org) => (
                <button
                  key={org.id}
                  onClick={() => setCurrentOrg(org)}
                  className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between transition ${
                    currentOrg?.id === org.id
                      ? "bg-blue-600/15 text-blue-400 font-medium"
                      : "text-slate-300 hover:bg-[#151e2e]"
                  }`}
                >
                  <span className="truncate">{org.name}</span>
                  <span className="text-[10px] font-mono text-slate-500">{org.role}</span>
                </button>
              ))}
              <div className="border-t border-[#1e293b] my-1" />
              <Link
                href="/organizations/new"
                className="w-full text-left px-3 py-1.5 text-xs text-blue-400 hover:bg-[#151e2e] flex items-center gap-1.5 transition"
              >
                <Plus className="w-3 h-3" />
                <span>Create Organization</span>
              </Link>
            </div>
          </div>
        )}

        {/* Global Search */}
        <div className="relative w-80 hidden md:block">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search flags, environments, repos..."
            className="w-full bg-[#151e2e] border border-[#1e293b] rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/60 transition-colors"
          />
        </div>
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-2 md:gap-4">
        {/* Status Indicator */}
        <div className="flex items-center gap-2 px-2 md:px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Tenant Isolated</span>
        </div>

        {/* User Profile or Login */}
        {user ? (
          <div className="flex items-center gap-2 md:gap-3 pl-2 border-l border-[#1e293b]">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-semibold text-white">
                {user.full_name ? user.full_name.slice(0, 2).toUpperCase() : user.email.slice(0, 2).toUpperCase()}
              </div>
              <div className="text-left text-xs leading-tight hidden lg:block">
                <p className="font-medium text-slate-200">{user.full_name || "Engineer"}</p>
                <p className="text-[10px] text-slate-400 truncate max-w-[140px]">{user.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-[#151e2e] transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </Link>
        )}
      </div>
    </header>
  );
}
