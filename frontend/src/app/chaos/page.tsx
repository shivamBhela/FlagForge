"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  FlaskConical,
  Play,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Plus,
  Clock,
  Radio,
} from "lucide-react";

export default function ChaosLabPage() {
  const { currentOrg } = useAuth();
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const loadData = async () => {
    if (!currentOrg) return;
    try {
      const [scList, rList] = await Promise.all([
        api.chaos.listScenarios(currentOrg.id),
        api.chaos.listRuns(currentOrg.id),
      ]);
      setScenarios(scList);
      setRuns(rList);
    } catch (e) {
      // Ignore
    }
  };

  useEffect(() => {
    loadData();
  }, [currentOrg]);

  const handleRunScenario = async (scenarioId: string) => {
    if (!currentOrg) return;
    setRunningId(scenarioId);
    setError("");
    setSuccessMsg("");
    try {
      await api.chaos.runScenario(currentOrg.id, scenarioId);
      setSuccessMsg(`Synthetic staging simulation completed. No load was sent and no remote flag changed.`);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Simulation failed.");
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-emerald-400" />
            <span>Chaos Lab — Controlled Staging Sandbox</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Synthetic examples only: no application load is sent and no Flagsmith state is changed or restored.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] px-2.5 py-1 rounded-full font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" /> Production Lock Active
          </span>
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

      {/* Scenarios Grid */}
      <div className="space-y-4">
        <h2 className="text-base font-bold text-white">Active Simulation Scenarios ({scenarios.length})</h2>
        {scenarios.length === 0 ? (
          <div className="text-center py-12 rounded-xl bg-[#0c121e] border border-[#1e293b] text-slate-500 text-xs">
            No chaos scenarios configured. Run a demo seed or add a staging scenario.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {scenarios.map((scen) => (
              <div
                key={scen.id}
                className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] hover:border-slate-700 transition flex flex-col justify-between space-y-4"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-bold text-white text-sm">{scen.name}</h3>
                      <p className="text-xs text-slate-400 mt-1">{scen.description}</p>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                      {scen.environment_name}
                    </span>
                  </div>

                  <div className="mt-4 p-3 rounded-lg bg-[#151e2e] border border-[#1e293b] text-xs space-y-1 font-mono">
                    <div className="text-slate-400">Target Flag: <span className="text-white font-bold">{scen.target_flag_key}</span></div>
                    <div className="text-slate-400">Injected Pattern: <span className="text-purple-400">{scen.scenario_type}</span></div>
                    <div className="text-slate-400">Load Rate: <span className="text-white">{scen.test_traffic_rate} req/s</span> ({scen.duration_seconds}s)</div>
                  </div>
                </div>

                <button
                  onClick={() => handleRunScenario(scen.id)}
                  disabled={runningId === scen.id}
                  className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm disabled:opacity-50"
                >
                  <Play className={`w-3.5 h-3.5 ${runningId === scen.id ? "animate-spin" : ""}`} />
                  <span>{runningId === scen.id ? "Running synthetic simulation..." : "Run Synthetic Test"}</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Historical Runs */}
      <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Clock className="w-4 h-4 text-blue-400" />
          <span>Synthetic Simulation Runs ({runs.length})</span>
        </h2>

        {runs.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">No simulation runs executed yet.</div>
        ) : (
          <div className="space-y-3">
            {runs.map((r) => (
              <div key={r.id} className="p-4 rounded-lg bg-[#151e2e] border border-[#1e293b] text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {r.status}
                    </span>
                    <span className="text-slate-300 font-mono font-bold">
                  {r.restored_verified ? "External Restoration Verified" : "Synthetic only — no restoration performed"}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">{new Date(r.created_at).toLocaleString()}</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center p-2 rounded bg-[#0c121e] border border-[#1e293b] font-mono text-[11px]">
                  <div>
                    <div className="text-slate-400">Synthetic baseline err</div>
                    <div className="text-emerald-400 font-bold">{(r.baseline_error_rate * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Synthetic scenario err</div>
                    <div className="text-rose-400 font-bold">{(r.simulated_error_rate * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Synthetic baseline p95</div>
                    <div className="text-emerald-400 font-bold">{r.baseline_p95_ms}ms</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Synthetic scenario p95</div>
                    <div className="text-amber-400 font-bold">{r.simulated_p95_ms}ms</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
