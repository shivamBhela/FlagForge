"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  Activity,
  RefreshCw,
  TrendingUp,
} from "lucide-react";

export default function LiveMonitorPage() {
  const { currentOrg } = useAuth();
  const [metrics, setMetrics] = useState<any | null>(null);
  const [selectedFlag, setSelectedFlag] = useState("checkout_v2_redesign");
  const [selectedEnvironment, setSelectedEnvironment] = useState("staging");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadMetrics = async () => {
    if (!currentOrg) return;
    setLoading(true);
    setLoadError(null);
    try {
      const data = await api.telemetry.getMetrics(currentOrg.id, selectedFlag, selectedEnvironment);
      setMetrics(data);
    } catch (e) {
      setMetrics(null);
      setLoadError(e instanceof Error ? e.message : "Metrics could not be loaded.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
  }, [currentOrg, selectedFlag, selectedEnvironment]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            <span>Live Monitor & OpenTelemetry Telemetry</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time feature-attributed telemetry ingested through OpenTelemetry Collector (:4318).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="monitor-environment" className="text-xs text-slate-400">Environment</label>
          <select id="monitor-environment" value={selectedEnvironment}
            onChange={(event) => setSelectedEnvironment(event.target.value)}
            className="px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-xs text-white">
            <option value="development">Development</option>
            <option value="staging">Staging</option>
            <option value="production">Production</option>
          </select>
          <button
            onClick={loadMetrics}
            disabled={loading || !currentOrg}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-xs font-medium text-slate-300 hover:text-white hover:bg-[#1f2937] transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh Metrics</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-5">
        <div className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b]">
          <span className="text-xs font-semibold uppercase text-slate-400">Attributed Requests</span>
          <div className="text-2xl font-bold text-white mt-2">
            {loading ? "Loading…" : metrics?.has_telemetry ? metrics.total_requests.toLocaleString() : "—"}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Requests in the selected environment</p>
        </div>
        <div className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b]">
          <span className="text-xs font-semibold uppercase text-slate-400">Average Error Rate</span>
          <div className="text-2xl font-bold text-emerald-400 mt-2">
            {loading ? "Loading…" : metrics?.has_telemetry ? `${(metrics.avg_error_rate * 100).toFixed(2)}%` : "—"}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Safety threshold: 5.0%</p>
        </div>
        <div className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b]">
          <span className="text-xs font-semibold uppercase text-slate-400">p95 Latency</span>
          <div className="text-2xl font-bold text-blue-400 mt-2">
            {loading ? "Loading…" : metrics?.has_latency_histogram && metrics.avg_p95_ms !== null ? `${metrics.avg_p95_ms}ms` : "—"}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Target threshold: ≤500ms</p>
        </div>
        <div className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b]">
          <span className="text-xs font-semibold uppercase text-slate-400">Sample Count</span>
          <div className="text-2xl font-bold text-purple-400 mt-2">
            {loading ? "Loading…" : metrics?.has_telemetry ? `${metrics.samples_count} windows` : "0 windows"}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">5-minute rolling aggregation</p>
        </div>
      </div>

      {/* Telemetry Stream */}
      <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-blue-400" />
          <span>Real-time Window Telemetry — {selectedFlag}</span>
        </h2>

        {loading ? (
          <div role="status" className="text-center py-10 text-slate-400 text-xs">Loading telemetry…</div>
        ) : loadError ? (
          <div role="alert" className="text-center py-10 text-rose-300 text-xs">{loadError}</div>
        ) : metrics?.has_telemetry && metrics.series?.length ? (
          <div className="divide-y divide-[#1e293b]">
            {metrics.series.map((s: any, idx: number) => (
              <div key={idx} className="py-3 flex items-center justify-between text-xs">
                <span className="font-mono text-slate-400">{new Date(s.time).toLocaleTimeString()}</span>
                <span className="font-mono text-white font-bold">{s.requests} reqs</span>
                <span className={`font-mono font-bold ${s.error_rate > 0.05 ? "text-rose-400" : "text-emerald-400"}`}>
                  {(s.error_rate * 100).toFixed(2)}% errors
                </span>
                <span className="font-mono text-blue-400">{s.p95_ms}ms p95</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-10 text-slate-500 text-xs">
            <div className="font-semibold text-slate-300">No telemetry received for {selectedFlag}.</div>
            <div className="mt-2">This is insufficient data, not evidence of healthy behavior. Generate traffic in a configured environment and refresh.</div>
          </div>
        )}
      </div>
    </div>
  );
}
