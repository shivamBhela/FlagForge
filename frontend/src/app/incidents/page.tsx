"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  AlertTriangle,
  Clock,
  Sparkles,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";

export default function IncidentsPage() {
  const { currentOrg } = useAuth();
  const [incidents, setIncidents] = useState<any[]>([]);
  const [actions, setActions] = useState<any[]>([]);
  const [explanation, setExplanation] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const [incList, actList] = await Promise.all([
        api.incidents.listIncidents(currentOrg.id),
        api.incidents.listRollbackActions(currentOrg.id),
      ]);
      setIncidents(incList);
      setActions(actList);

      if (incList.length > 0) {
        const exp = await api.incidents.explain(currentOrg.id, incList[0].flag_key);
        setExplanation(exp);
      }
    } catch (e) {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!currentOrg) return;
    let ignore = false;
    const fetchData = async () => {
      setLoading(true);
      try {
        const [incidentList, actionList] = await Promise.all([
          api.incidents.listIncidents(currentOrg.id),
          api.incidents.listRollbackActions(currentOrg.id),
        ]);
        if (ignore) return;
        setIncidents(incidentList);
        setActions(actionList);
        setExplanation(incidentList.length > 0
          ? await api.incidents.explain(currentOrg.id, incidentList[0].flag_key)
          : null);
      } catch {
        // Keep the last successful history visible when a refresh fails.
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    void fetchData();
    return () => {
      ignore = true;
    };
  }, [currentOrg]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-rose-400" />
            <span>Incidents & Post-Mortem Audit Trail</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Auditable incident records, rollback history (when available), and advisory explanations.
          </p>
        </div>
      </div>

      {/* Hybrid AI Explanation Pane */}
      {explanation && (
        <div className="p-6 rounded-2xl bg-[#0c121e] border border-purple-500/30 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <h2 className="text-sm font-bold text-white">Hybrid Post-Mortem Explanation</h2>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">
              Advisory / Read-Only Fallback
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">{explanation.summary}</p>

          <div className="pt-2 border-t border-[#1e293b]">
            <span className="text-[11px] font-semibold uppercase text-slate-500">Recommended Remediation:</span>
            <ul className="mt-1 space-y-1 text-xs text-slate-400 list-disc list-inside">
              {explanation.recommended_actions.map((act: string, idx: number) => (
                <li key={idx}>{act}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Incidents & Actions Lists */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Recorded Incidents ({incidents.length})</span>
          </h2>
          {incidents.length === 0 ? (
            <div className="text-center py-10 text-slate-500 text-xs">No active incidents recorded.</div>
          ) : (
            <div className="space-y-3">
              {incidents.map((inc) => (
                <div key={inc.id} className="p-3.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{inc.title}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                      {inc.severity}
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px]">{inc.description}</p>
                  <div className="text-[10px] text-slate-500 font-mono">{new Date(inc.created_at).toLocaleString()}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <RotateCcw className="w-4 h-4 text-blue-400" />
            <span>Verified Rollback Executions ({actions.length})</span>
          </h2>
          {actions.length === 0 ? (
            <div className="text-center py-10 text-slate-500 text-xs">No rollback actions executed.</div>
          ) : (
            <div className="space-y-3">
              {actions.map((act) => (
                <div key={act.id} className="p-3.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-white font-bold">{act.flag_key}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {act.status}
                    </span>
                  </div>
                  <div className="text-slate-400 text-[11px] font-mono">
                    Target: enabled=false | By: {act.executed_by}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">{new Date(act.created_at).toLocaleString()}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
