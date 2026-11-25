"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  ShieldAlert,
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
  const [evaluating, setEvaluating] = useState(false);

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
            Deterministic risk evaluation and policy review. Remote rollback is disabled until provider write and verification are implemented.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[11px] px-2.5 py-1 rounded-full font-mono bg-[#151e2e] text-slate-300 border border-[#1e293b]">
            Mode: {policy?.mode || "AUTOMATIC"}
          </span>
          <span className="text-[11px] px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Rollback unavailable
          </span>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 shrink-0" />
        <span>No remote flag change will be attempted. Risk results are advisory and do not authorize a rollback.</span>
      </div>

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
            <p className={`text-xs mt-2 ${riskAssessment.factors?.telemetry_confidence === "SUFFICIENT" ? "text-emerald-400" : "text-amber-400"}`}>
              Telemetry confidence: {riskAssessment.factors?.telemetry_confidence || "Unknown"}
              {riskAssessment.factors?.telemetry_request_count !== undefined && ` (${riskAssessment.factors.telemetry_request_count} requests)`}
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

      <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-3">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Lock className="w-4 h-4 text-amber-400" />
          <span>Safety boundary</span>
        </h2>
        <p className="text-xs text-slate-400">
          The API exposes risk and policy records. Redis-backed locks and verified Flagsmith rollback are not implemented in this checkout, so the UI does not offer a rollback action.
        </p>
      </div>
    </div>
  );
}
