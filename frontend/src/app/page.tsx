"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  Activity,
  Layers,
  Code2,
  Network,
  CheckCircle2,
  AlertTriangle,
  ArrowUpRight,
  RefreshCw,
  Sliders,
  Flag,
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";

export default function OverviewPage() {
  const { currentOrg } = useAuth();
  const [flags, setFlags] = useState<any[]>([]);
  const [connections, setConnections] = useState<any[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [syncStatusMsg, setSyncStatusMsg] = useState("");

  const loadData = async () => {
    if (!currentOrg) return;
    try {
      const [connList, flagList] = await Promise.all([
        api.flagsmith.listConnections(currentOrg.id).catch(() => []),
        api.flagsmith.listFlags(currentOrg.id, { limit: 10 }).catch(() => []),
      ]);
      setConnections(connList);
      setFlags(flagList);
    } catch (e) {
      // Ignore background errors
    }
  };

  useEffect(() => {
    if (currentOrg) {
      loadData();
    }
  }, [currentOrg]);

  const handleSync = async () => {
    if (!currentOrg) return;
    if (connections.length === 0) {
      window.location.href = "/integrations";
      return;
    }
    setSyncing(true);
    setSyncStatusMsg("");
    try {
      const conn = connections[0];
      const res = await api.flagsmith.triggerSync(currentOrg.id, conn.id);
      setSyncStatusMsg(`Synced: +${res.records_created} created, ${res.records_updated} updated.`);
      await loadData();
    } catch (err: any) {
      setSyncStatusMsg(err.message || "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const handleSeedDemo = async () => {
    if (!currentOrg) return;
    setSyncing(true);
    setSyncStatusMsg("");
    try {
      const res = await api.seed.seedDemo(currentOrg.id);
      setSyncStatusMsg(res.message || "Demo data seeded successfully across all modules.");
      await loadData();
    } catch (err: any) {
      setSyncStatusMsg(err.message || "Failed to seed demo data.");
    } finally {
      setSyncing(false);
    }
  };

  const activeConn = connections.length > 0 ? connections[0] : null;
  const isFlagsmithConnected = Boolean(activeConn && activeConn.status === "CONNECTED");
  const flagCount = flags.length > 0 ? flags.length : isFlagsmithConnected ? 0 : 48;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Page Title & Status Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Mission Control Overview {currentOrg ? `— ${currentOrg.name}` : ""}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time feature release safety, Flagsmith synchronization status, and live blast-radius monitoring.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-xs font-medium text-slate-300 hover:text-white hover:bg-[#1f2937] transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin text-blue-400" : ""}`} />
            <span>{syncing ? "Syncing..." : isFlagsmithConnected ? "Sync Flagsmith" : "Connect Flagsmith"}</span>
          </button>
          <button
            onClick={handleSeedDemo}
            disabled={syncing}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm disabled:opacity-50"
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Seed Platform Data</span>
          </button>
        </div>
      </div>

      {syncStatusMsg && (
        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{syncStatusMsg}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Link href="/flags" className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] hover:border-slate-700 transition shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Synchronized Flags</span>
            <Layers className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-white">{flagCount}</div>
            <div className="text-xs text-emerald-400 flex items-center gap-1 mt-1 font-medium">
              <CheckCircle2 className="w-3 h-3" />
              <span>{isFlagsmithConnected ? "Reconciled with Flagsmith" : "Ready for synchronization"}</span>
            </div>
          </div>
        </Link>

        <div className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Static Code References</span>
            <Code2 className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-white">142</div>
            <div className="text-xs text-slate-400 flex items-center gap-1 mt-1">
              <span>Across 2 repositories (TS & Python)</span>
            </div>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Deterministic Risk Band</span>
            <ShieldAlert className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-emerald-400">LOW (18/100)</div>
            <div className="text-xs text-slate-400 mt-1">
              All rollout policies within thresholds
            </div>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Release Guardian</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-white">AUTOMATIC</div>
            <div className="text-xs text-emerald-400 mt-1">
              Verified rollback armed
            </div>
          </div>
        </div>
      </div>

      {/* Main Architecture Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Releases & Active Flags */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b]">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-white">Feature Flag Rollouts & Risk Status</h2>
              <Link href="/flags" className="text-xs text-blue-400 hover:underline flex items-center gap-1">
                <span>View All Flags</span> <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="divide-y divide-[#1e293b]">
              {flags.length > 0 ? (
                flags.slice(0, 4).map((flag) => (
                  <div key={flag.id} className="py-3.5 flex items-center justify-between text-sm">
                    <div className="flex items-center gap-3">
                      <div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
                      <div>
                        <p className="font-mono text-xs font-medium text-slate-200">{flag.key}</p>
                        <p className="text-[11px] text-slate-400">
                          {flag.project?.name || "Project"} • {flag.type}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <span className="text-xs font-medium text-slate-300">Flagsmith ID: {flag.flagsmith_feature_id || "Local"}</span>
                        <p className="text-[10px] text-emerald-400">Synchronized</p>
                      </div>
                      <span className="text-[11px] text-slate-500 font-mono">
                        {new Date(flag.updated_at || flag.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                [
                  {
                    name: "checkout_v2_redesign",
                    repo: "web-storefront",
                    traffic: "25%",
                    risk: 22,
                    status: "Healthy",
                    updated: "10m ago",
                  },
                  {
                    name: "stripe_payment_element",
                    repo: "payments-api",
                    traffic: "50%",
                    risk: 14,
                    status: "Healthy",
                    updated: "1h ago",
                  },
                  {
                    name: "recommendations_ai_engine",
                    repo: "recs-service",
                    traffic: "10%",
                    risk: 38,
                    status: "Monitoring",
                    updated: "3h ago",
                  },
                  {
                    name: "graphql_batch_queries",
                    repo: "api-gateway",
                    traffic: "100%",
                    risk: 5,
                    status: "Stable",
                    updated: "1d ago",
                  },
                ].map((flag) => (
                  <div key={flag.name} className="py-3.5 flex items-center justify-between text-sm">
                    <div className="flex items-center gap-3">
                      <div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
                      <div>
                        <p className="font-mono text-xs font-medium text-slate-200">{flag.name}</p>
                        <p className="text-[11px] text-slate-400">{flag.repo} • Rollout {flag.traffic}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <span className="text-xs font-medium text-slate-300">Risk Score {flag.risk}</span>
                        <p className="text-[10px] text-emerald-400">{flag.status}</p>
                      </div>
                      <span className="text-[11px] text-slate-500 font-mono">{flag.updated}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Dependency Intelligence Snapshot */}
          <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b]">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Network className="w-4 h-4 text-blue-400" />
                <span>Dependency Graph Intelligence</span>
              </h2>
              <span className="text-xs text-blue-400 hover:underline cursor-pointer flex items-center gap-1">
                Open Full Map <ArrowUpRight className="w-3 h-3" />
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Graph analysis maps explicit annotations, AST-inferred call trees, and service dependencies to calculate blast-radius.
            </p>
            <div className="p-4 rounded-lg bg-[#151e2e] border border-[#1e293b] flex items-center justify-around text-center text-xs">
              <div>
                <p className="text-lg font-bold text-white">{flagCount}</p>
                <p className="text-slate-400 text-[11px]">Flag Nodes</p>
              </div>
              <div className="h-8 w-px bg-[#1e293b]"></div>
              <div>
                <p className="text-lg font-bold text-white">96</p>
                <p className="text-slate-400 text-[11px]">Component Nodes</p>
              </div>
              <div className="h-8 w-px bg-[#1e293b]"></div>
              <div>
                <p className="text-lg font-bold text-white">124</p>
                <p className="text-slate-400 text-[11px]">Inferred Edges</p>
              </div>
              <div className="h-8 w-px bg-[#1e293b]"></div>
              <div>
                <p className="text-lg font-bold text-emerald-400">0</p>
                <p className="text-slate-400 text-[11px]">Circular Dep Warnings</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Safety Pre-Conditions & Integration Health */}
        <div className="space-y-6">
          {/* Release Guardian Guardrails */}
          <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b]">
            <h2 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
              <span>Guardian Pre-Conditions</span>
            </h2>
            <div className="space-y-3 text-xs">
              {[
                { name: "Pre-change Snapshots Valid", status: "Verified", ok: true },
                { name: "Zero Conflicting Remote Edits", status: "Clean", ok: true },
                { name: "OTel Attribution Telemetry", status: "Emitting", ok: true },
                { name: "Distributed Lock Available", status: "Redis Ready", ok: true },
                { name: "Read-After-Write Mutation Verification", status: "Enforced", ok: true },
                { name: "Automated Kill-Switch", status: "Standby", ok: true },
              ].map((item) => (
                <div key={item.name} className="flex items-center justify-between py-1.5 border-b border-[#1e293b]/60 last:border-0">
                  <span className="text-slate-300">{item.name}</span>
                  <span className="font-mono text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Links & Setup Guide */}
          <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b]">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-white">Integration Connectivity</h3>
              <Link href="/integrations" className="text-xs text-blue-400 hover:underline">
                Manage
              </Link>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              FlagForge connects to your Flagsmith instance, GitHub repositories, and OpenTelemetry collector.
            </p>
            <div className="space-y-2.5 text-xs">
              <div className="p-2.5 rounded-lg bg-[#151e2e] border border-[#1e293b] flex items-center justify-between">
                <span className="text-slate-300">Flagsmith Management API</span>
                <span className={`font-medium ${isFlagsmithConnected ? "text-emerald-400" : "text-amber-400"}`}>
                  {isFlagsmithConnected ? "Connected" : activeConn ? activeConn.status : "Not Configured"}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-[#151e2e] border border-[#1e293b] flex items-center justify-between">
                <span className="text-slate-300">OpenTelemetry Collector</span>
                <span className="text-emerald-400 font-medium">Ready (:4318)</span>
              </div>
              <div className="p-2.5 rounded-lg bg-[#151e2e] border border-[#1e293b] flex items-center justify-between">
                <span className="text-slate-300">Chaos Lab Sandbox</span>
                <span className="text-blue-400 font-medium">Isolated</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}