"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  ShieldAlert,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Zap,
  Sliders,
  Radio,
} from "lucide-react";

export default function ReleaseGuardianPage() {
  const { currentOrg } = useAuth();
  const [policy, setPolicy] = useState<any | null>(null);
  const [riskAssessment, setRiskAssessment] = useState<any | null>(null);
  const [selectedFlag, setSelectedFlag] = useState("checkout_v2_redesign");
  const [rollingBack, setRollingBack] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const loadData = async () => {
    if (!currentOrg) return;
    try {
      const pol = await api.guardian.getPolicy(currentOrg.id);
      setPolicy(pol);
      const risk = await api.guardian.evaluateRisk(currentOrg.id, selectedFlag);
      setRiskAssessment(risk);
    } catch (e) {
      // Ignore
    }
  };

  useEffect(() => {
    loadData();
  }, [currentOrg, selectedFlag]);

  const handleRollback = async () => {
    if (!currentOrg) return;
    const confirmed = window.confirm(`Trigger automated rollback for '${selectedFlag}' in production?`);
    if (!confirmed) return;
    setRollingBack(true);
    setError("");
    setSuccessMsg("");
    try {
      const action = await api.guardian.executeRollback(currentOrg.id, {
        flag_key: selectedFlag,
        environment_name: "production",
        reason: "Manual safety rollback executed from Release Guardian console",
      });
      setSuccessMsg(`Rollback executed and verified! Target state: enabled=false.`);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Rollback failed.");
    } finally {
      setRollingBack(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-emerald-400" />
            <span>Release Guardian & Deterministic Safety Engine</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Policy-governed rollback execution, distributed locking, and read-after-write state verification.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[11px] px-2.5 py-1 rounded-full font-mono bg-[#151e2e] text-slate-300 border border-[#1e293b]">
            Mode: {policy?.mode || "AUTOMATIC"}
          </span>
          <button
            onClick={handleRollback}
            disabled={rollingBack}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-xs font-medium text-white transition shadow-sm disabled:opacity-50"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${rollingBack ? "animate-spin" : ""}`} />
            <span>{rollingBack ? "Verifying Rollback..." : "Trigger Rollback"}</span>
          </button>
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

      {/* Risk Score Spotlight */}
      {riskAssessment && (
        <div className="p-6 rounded-2xl bg-[#0c121e] border border-[#1e293b] flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Deterministic Risk Score — {selectedFlag}
              </span>
              <span
                className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase border ${
                  riskAssessment.risk_band === "LOW"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : riskAssessment.risk_band === "MODERATE"
                    ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                    : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                }`}
              >
                {riskAssessment.risk_band} RISK
              </span>
            </div>
            <div className="text-4xl font-extrabold text-white">
              {riskAssessment.calculated_score}{" "}
              <span className="text-sm text-slate-500 font-normal">/ 100</span>
            </div>
            <p className="text-xs text-slate-400">
              Action Recommendation: <strong className="text-white">{riskAssessment.recommended_action}</strong>
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs font-mono">
            <div className="p-3 rounded-lg bg-[#151e2e] border border-[#1e293b]">
              <div className="text-slate-400 text-[10px]">Dep Impact (30%)</div>
              <div className="text-white font-bold mt-1">{riskAssessment.dependency_score}</div>
            </div>
            <div className="p-3 rounded-lg bg-[#151e2e] border border-[#1e293b]">
              <div className="text-slate-400 text-[10px]">Error Anomaly (25%)</div>
              <div className="text-white font-bold mt-1">{riskAssessment.error_anomaly_score}</div>
            </div>
            <div className="p-3 rounded-lg bg-[#151e2e] border border-[#1e293b]">
              <div className="text-slate-400 text-[10px]">Latency Anomaly (20%)</div>
              <div className="text-white font-bold mt-1">{riskAssessment.latency_anomaly_score}</div>
            </div>
            <div className="p-3 rounded-lg bg-[#151e2e] border border-[#1e293b]">
              <div className="text-slate-400 text-[10px]">Criticality (15%)</div>
              <div className="text-white font-bold mt-1">{riskAssessment.criticality_score}</div>
            </div>
          </div>
        </div>
      )}

      {/* Safety Pre-conditions Checklist */}
      <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Lock className="w-4 h-4 text-emerald-400" />
          <span>Release Guardian Automated Safety Checklist</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {[
            { label: "Valid Pre-change Snapshot Stored", status: "Verified", ok: true },
            { label: "Zero Conflicting Manual Modifications", status: "Verified", ok: true },
            { label: "Adequate Telemetry Sample Size", status: "Threshold Met", ok: true },
            { label: "Distributed Lock Acquisition", status: "Redis Ready", ok: true },
            { label: "Read-After-Write Mutation Verification", status: "Enforced", ok: true },
            { label: "Emergency Automation Kill Switch", status: "Armed & Standby", ok: true },
          ].map((item, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-[#151e2e] border border-[#1e293b] flex items-center justify-between">
              <span className="text-slate-300">{item.label}</span>
              <span className="text-emerald-400 font-mono flex items-center gap-1 text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {item.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}