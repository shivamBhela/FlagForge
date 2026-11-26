"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  Flag,
  Search,
  RefreshCw,
  FolderGit2,
  Lock,
  Layers,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Sliders,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";

export default function FeatureFlagsPage() {
  const { currentOrg, isLoading: authLoading } = useAuth();
  const [flags, setFlags] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const loadData = async () => {
    if (!currentOrg) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [projList, flagList] = await Promise.all([
        api.projects.list(currentOrg.id),
        api.flagsmith.listFlags(currentOrg.id, {
          project_id: selectedProject || undefined,
          query: searchQuery.trim() || undefined,
        }),
      ]);
      setProjects(projList);
      setFlags(flagList);
    } catch (err: any) {
      setError(err.message || "Failed to load feature flags.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentOrg) {
      loadData();
    } else {
      setLoading(false);
    }
  }, [currentOrg, selectedProject]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleQuickSync = async () => {
    if (!currentOrg) return;
    setSyncing(true);
    setError("");
    setSuccessMsg("");
    try {
      // Find connections first
      const conns = await api.flagsmith.listConnections(currentOrg.id);
      if (conns.length === 0) {
        setError("No Flagsmith instance connected yet. Go to Integrations to connect one.");
        return;
      }
      const conn = conns[0];
      const res = await api.flagsmith.triggerSync(currentOrg.id, conn.id);
      setSuccessMsg(
        `Synchronized from Flagsmith: ${res.records_created} created, ${res.records_updated} updated, ${res.records_unchanged} unchanged.`
      );
      await loadData();
    } catch (err: any) {
      setError(err.message || "Sync failed.");
    } finally {
      setSyncing(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="flex items-center gap-3 text-slate-400 text-xs font-medium">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span>Loading synchronized feature flags...</span>
        </div>
      </div>
    );
  }

  if (!currentOrg) {
    return (
      <div className="max-w-md mx-auto text-center py-16">
        <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 mx-auto mb-4">
          <Flag className="w-6 h-6" />
        </div>
        <h2 className="text-base font-semibold text-white">No Organization Selected</h2>
        <p className="text-xs text-slate-400 mt-1 mb-6">
          Please select or create an organization to inspect synchronized feature flags.
        </p>
        <Link
          href="/organizations/new"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition"
        >
          <span>Create Organization</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Flag className="w-5 h-5 text-blue-400" />
            <span>Feature Flags Explorer — {currentOrg.name}</span>
          </h1>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[11px] px-2 py-0.5 rounded-full font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" /> Authoritative Remote: Flagsmith
            </span>
            <span className="text-xs text-slate-400">
              Synchronized snapshot with per-environment states & release risk metadata.
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleQuickSync}
            disabled={syncing}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#151e2e] hover:bg-[#1f2937] border border-[#1e293b] text-xs font-medium text-slate-200 hover:text-white transition shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin text-blue-400" : ""}`} />
            <span>{syncing ? "Reconciling..." : "Reconcile Flagsmith"}</span>
          </button>

          <Link
            href="/integrations"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Integrations</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-[#0c121e] border border-[#1e293b] flex flex-col md:flex-row md:items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search flags by key, name, or description (press Enter)..."
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-blue-500 font-mono"
          />
        </form>

        <div className="flex items-center gap-3">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="">All Projects ({projects.length})</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Feature Flags List */}
      {flags.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-[#1e293b] rounded-2xl p-8 bg-[#0c121e]">
          <Flag className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-white">No Feature Flags Synchronized</h3>
          <p className="text-xs text-slate-400 mt-1 mb-5 max-w-md mx-auto">
            {searchQuery
              ? `No flags matched "${searchQuery}". Try a different search.`
              : "Connect Flagsmith in Integrations to discover and synchronize your remote feature flags."}
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              href="/integrations"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Configure Flagsmith Connection</span>
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {flags.map((flag) => {
            const projName = flag.project?.name || flag.project_name || "Unknown Project";
            return (
              <div
                key={flag.id}
                className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] hover:border-slate-700 transition space-y-4"
              >
                {/* Top flag meta */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-blue-400 mt-0.5">
                      <Flag className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-sm font-bold text-white tracking-wide">
                          {flag.key}
                        </span>
                        <button
                          onClick={() => handleCopyKey(flag.key)}
                          className="text-slate-500 hover:text-slate-300 transition"
                          title="Copy flag key"
                        >
                          {copiedKey === flag.key ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-[#151e2e] text-slate-300 border border-[#1e293b]">
                          {flag.type}
                        </span>
                        <span className="text-[11px] text-slate-400 flex items-center gap-1 font-sans">
                          in <FolderGit2 className="w-3 h-3 text-slate-500" /> {projName}
                        </span>
                      </div>
                      {flag.description && (
                        <p className="text-xs text-slate-400 mt-1">{flag.description}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right text-[11px] text-slate-500 font-mono">
                      <span>Flagsmith ID: {flag.flagsmith_feature_id || "N/A"}</span>
                    </div>
                  </div>
                </div>

                {/* Per-Environment States */}
                <div className="pt-3 border-t border-[#1e293b]/70">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
                    Environment States
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {flag.states && flag.states.length > 0 ? (
                      flag.states.map((st: any) => {
                        const envName = st.environment?.name || st.environment_name;
                        const isProd = st.environment?.is_production ?? st.is_production;
                        return (
                          <div
                            key={st.id}
                            className={`p-3 rounded-lg border transition ${
                              isProd
                                ? "bg-[#10192b] border-blue-500/30"
                                : "bg-[#151e2e] border-[#1e293b]"
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                                {isProd && (
                                  <span title="Production Protected">
                                    <Lock className="w-3 h-3 text-amber-400" />
                                  </span>
                                )}
                                <span>{envName || "Environment"}</span>
                              </span>
                              <span
                                className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border flex items-center gap-1 ${
                                  st.enabled
                                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                                    : "bg-slate-700/20 text-slate-400 border-slate-700/40"
                                }`}
                              >
                                {st.enabled ? (
                                  <>
                                    <CheckCircle2 className="w-2.5 h-2.5" />
                                    <span>ON</span>
                                  </>
                                ) : (
                                  <>
                                    <XCircle className="w-2.5 h-2.5" />
                                    <span>OFF</span>
                                  </>
                                )}
                              </span>
                            </div>

                            {st.value && (
                              <div className="text-[11px] font-mono text-purple-300 bg-[#0c121e] px-2 py-1 rounded border border-[#1e293b] truncate">
                                Val: {st.value}
                              </div>
                            )}

                            <div className="mt-2 text-[10px] text-slate-500 font-mono truncate">
                              State ID: {st.flagsmith_feature_state_id || "Local"}
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-xs text-slate-500 col-span-full">
                        No environment states recorded. Run synchronization from Integrations.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
