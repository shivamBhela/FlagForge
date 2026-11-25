"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  Sparkles,
  GitPullRequest,
  FileCode,
} from "lucide-react";

export default function CleanupStudioPage() {
  const { currentOrg } = useAuth();
  const [staleFlags, setStaleFlags] = useState<any[]>([]);
  const [patches, setPatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewPatch, setPreviewPatch] = useState<any | null>(null);

  const loadData = async () => {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const [stale, patchList] = await Promise.all([
        api.cleanup.getStaleFlags(currentOrg.id),
        api.cleanup.listPatches(currentOrg.id),
      ]);
      setStaleFlags(stale);
      setPatches(patchList);
    } catch (e) {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentOrg]);

  const handleGeneratePatch = async (flagKey: string, filePath: string) => {
    if (!currentOrg) return;
    try {
      const patch = await api.cleanup.generatePatch(currentOrg.id, {
        flag_key: flagKey,
        file_path: filePath,
      });
      setPreviewPatch(patch);
      await loadData();
    } catch (e: any) {
      alert(e.message || "Failed to generate patch.");
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-400" />
            <span>Cleanup Studio — Technical Debt Elimination</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Detect stale flags and create a human-reviewed local diff proposal. GitHub PR creation is not configured.
          </p>
        </div>
      </div>

      {/* Stale Candidates Grid */}
      <div className="space-y-4">
        <h2 className="text-base font-bold text-white">Stale Flag Elimination Candidates ({staleFlags.length})</h2>

        {staleFlags.length === 0 ? (
          <div className="text-center py-10 rounded-xl bg-[#0c121e] border border-[#1e293b] text-slate-500 text-xs">
            No stale flags identified. Codebase is clean and active.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {staleFlags.map((item) => (
              <div key={item.flag_key} className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-bold text-white">{item.flag_key}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      {item.references_count} References
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{item.reason}</p>
                </div>

                <button
                  onClick={() => handleGeneratePatch(item.flag_key, item.files[0] || "src/components/Checkout.tsx")}
                  className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm"
                >
                  <FileCode className="w-3.5 h-3.5" />
                  <span>Preview Cleanup Patch</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Patch Preview Modal / Box */}
      {previewPatch && (
        <div className="p-6 rounded-2xl bg-[#0c121e] border border-blue-500/40 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <GitPullRequest className="w-4 h-4 text-blue-400" />
              <span>Unified Diff Preview — {previewPatch.file_path}</span>
            </h3>
            <span className="text-[11px] text-amber-400">GitHub App integration not configured</span>
          </div>
          <pre className="p-4 rounded-xl bg-[#151e2e] border border-[#1e293b] text-xs font-mono text-emerald-300 overflow-x-auto">
            {previewPatch.diff_preview}
          </pre>
        </div>
      )}
    </div>
  );
}
