"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  Sliders,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Save,
} from "lucide-react";

export default function PoliciesPage() {
  const { currentOrg } = useAuth();
  const [policy, setPolicy] = useState<any | null>(null);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [error, setError] = useState("");

  const loadPolicy = async () => {
    if (!currentOrg) return;
    try {
      const pol = await api.guardian.getPolicy(currentOrg.id);
      setPolicy(pol);
    } catch (e) {
      // Ignore
    }
  };

  useEffect(() => {
    loadPolicy();
  }, [currentOrg]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg || !policy) return;
    setSaving(true);
    setError("");
    setSuccessMsg("");
    try {
      const updated = await api.guardian.updatePolicy(currentOrg.id, policy);
      setPolicy(updated);
      setSuccessMsg("Rollout policies and safety thresholds updated successfully.");
    } catch (err: any) {
      setError(err.message || "Failed to update policy.");
    } finally {
      setSaving(false);
    }
  };

  if (!policy) {
    return <div className="p-8 text-center text-xs text-slate-500">Loading platform policies...</div>;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-blue-400" />
            <span>Deterministic Risk Weights & Rollout Policies</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure advisory risk weights and thresholds. Automatic rollback is disabled and no mode changes provider state.
          </p>
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

      <form onSubmit={handleSave} className="p-6 rounded-2xl bg-[#0c121e] border border-[#1e293b] space-y-5">
        <div>
          <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">
            Rollback Enforcement Mode
          </label>
          <select
            value={policy.mode}
            onChange={(e) => setPolicy({ ...policy, mode: e.target.value })}
            className="w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="MONITOR">MONITOR (Record risk and notify, no actions)</option>
            <option value="NOTIFY">NOTIFY (Alert on critical risk)</option>
            <option value="APPROVAL_REQUIRED">APPROVAL_REQUIRED (Require human confirmation)</option>
            <option value="AUTOMATIC">AUTOMATIC (Advisory only; provider mutation disabled)</option>
          </select>
        </div>

        <div className="pt-3 border-t border-[#1e293b]">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            Formula Weights (Must sum to 1.00)
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-300 mb-1">Dependency Impact Weight</label>
              <input
                type="number"
                step="0.05"
                value={policy.weight_dependency_impact}
                onChange={(e) => setPolicy({ ...policy, weight_dependency_impact: parseFloat(e.target.value) })}
                className="w-full px-3 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-300 mb-1">Error Anomaly Weight</label>
              <input
                type="number"
                step="0.05"
                value={policy.weight_error_anomaly}
                onChange={(e) => setPolicy({ ...policy, weight_error_anomaly: parseFloat(e.target.value) })}
                className="w-full px-3 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-300 mb-1">Latency Anomaly Weight</label>
              <input
                type="number"
                step="0.05"
                value={policy.weight_latency_anomaly}
                onChange={(e) => setPolicy({ ...policy, weight_latency_anomaly: parseFloat(e.target.value) })}
                className="w-full px-3 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-300 mb-1">Change Criticality Weight</label>
              <input
                type="number"
                step="0.05"
                value={policy.weight_change_criticality}
                onChange={(e) => setPolicy({ ...policy, weight_change_criticality: parseFloat(e.target.value) })}
                className="w-full px-3 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white font-mono"
              />
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-[#1e293b]">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            Safety Anomaly Thresholds
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-300 mb-1">Max Error Rate Threshold (e.g. 0.05 = 5%)</label>
              <input
                type="number"
                step="0.01"
                value={policy.max_error_rate_threshold}
                onChange={(e) => setPolicy({ ...policy, max_error_rate_threshold: parseFloat(e.target.value) })}
                className="w-full px-3 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-300 mb-1">Max p95 Latency Threshold (ms)</label>
              <input
                type="number"
                value={policy.max_p95_latency_ms}
                onChange={(e) => setPolicy({ ...policy, max_p95_latency_ms: parseFloat(e.target.value) })}
                className="w-full px-3 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white font-mono"
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm disabled:opacity-50"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{saving ? "Saving Policies..." : "Save Policies"}</span>
        </button>
      </form>
    </div>
  );
}
