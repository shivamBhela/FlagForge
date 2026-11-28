"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  Code2,
  Play,
  FolderGit2,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Search,
  ExternalLink,
  Plus,
  RefreshCw,
  Sparkles,
} from "lucide-react";

export default function CodeScannerPage() {
  const { currentOrg } = useAuth();
  const [repositories, setRepositories] = useState<any[]>([]);
  const [scans, setScans] = useState<any[]>([]);
  const [references, setReferences] = useState<any[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const loadData = async () => {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const [repos, scList, refs] = await Promise.all([
        api.scanner.listRepositories(currentOrg.id),
        api.scanner.listScans(currentOrg.id),
        api.scanner.listReferences(currentOrg.id),
      ]);
      setRepositories(repos);
      setScans(scList);
      setReferences(refs);
      if (repos.length > 0 && !selectedRepo) {
        setSelectedRepo(repos[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load scanner data.");
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
        const [repos, scanList, refs] = await Promise.all([
          api.scanner.listRepositories(currentOrg.id),
          api.scanner.listScans(currentOrg.id),
          api.scanner.listReferences(currentOrg.id),
        ]);
        if (ignore) return;
        setRepositories(repos);
        setScans(scanList);
        setReferences(refs);
        if (repos.length > 0) {
          setSelectedRepo((previousRepo) => previousRepo || repos[0].id);
        }
      } catch (loadError: any) {
        if (!ignore) setError(loadError.message || "Failed to load scanner data.");
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    void fetchData();
    return () => {
      ignore = true;
    };
  }, [currentOrg]);

  const handleTriggerScan = async () => {
    if (!currentOrg) return;
    let repoId = selectedRepo;
    setScanning(true);
    setError("");
    setSuccessMsg("");
    try {
      if (!repoId && repositories.length === 0) {
        // Auto create demo repository
        const newRepo = await api.scanner.createRepository(currentOrg.id, {
          name: "web-storefront",
          repo_url: "https://example.invalid/flagforge/demo-web-storefront",
          language: "typescript",
        });
        repoId = newRepo.id;
      }
      const scan = await api.scanner.triggerScan(currentOrg.id, repoId);
      setSuccessMsg(`Scan completed! Discovered ${scan.findings_count} flag references across ${scan.files_scanned} files.`);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Scan failed.");
    } finally {
      setScanning(false);
    }
  };

  const filteredReferences = references.filter(
    (r) =>
      r.flag_key.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.file_path.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Code2 className="w-5 h-5 text-purple-400" />
            <span>Code Intelligence & Static AST Scanner</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Tree-sitter and AST parsing across TypeScript, JavaScript, and Python discovering real flag references.
          </p>
        </div>

        <button
          onClick={handleTriggerScan}
          disabled={scanning}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 ${scanning ? "animate-spin" : ""}`} />
          <span>{scanning ? "Scanning AST..." : "Run AST Scan"}</span>
        </button>
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

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b]">
          <span className="text-xs font-semibold uppercase text-slate-400">Total Code References</span>
          <div className="text-2xl font-bold text-white mt-2">{references.length}</div>
          <p className="text-[11px] text-slate-500 mt-1">Extracted with AST & Lexer confidence</p>
        </div>
        <div className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b]">
          <span className="text-xs font-semibold uppercase text-slate-400">Scanned Repositories</span>
          <div className="text-2xl font-bold text-white mt-2">{repositories.length}</div>
          <p className="text-[11px] text-slate-500 mt-1">Monitored across git branches</p>
        </div>
        <div className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b]">
          <span className="text-xs font-semibold uppercase text-slate-400">Historical Scans</span>
          <div className="text-2xl font-bold text-emerald-400 mt-2">{scans.length}</div>
          <p className="text-[11px] text-slate-500 mt-1">100% completed without execution risk</p>
        </div>
      </div>

      {/* Search & References Table */}
      <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <FileCode className="w-4 h-4 text-blue-400" />
            <span>Discovered Feature Flag References ({filteredReferences.length})</span>
          </h2>
          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by flag key or file..."
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs font-mono focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {filteredReferences.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-xs">
            No code references discovered yet. Click &quot;Run AST Scan&quot; to analyze your repository.
          </div>
        ) : (
          <div className="divide-y divide-[#1e293b] overflow-x-auto">
            {filteredReferences.map((ref) => (
              <div key={ref.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs font-bold text-white bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                      {ref.flag_key}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {ref.file_path}:{ref.line_number}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#151e2e] text-slate-300 font-mono">
                      scope: {ref.symbol_name || "module"}
                    </span>
                  </div>
                  {ref.evidence_snippet && (
                    <pre className="text-[11px] text-slate-300 font-mono bg-[#151e2e] p-2 rounded border border-[#1e293b] overflow-x-auto">
                      {ref.evidence_snippet}
                    </pre>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {Math.round(ref.parser_confidence * 100)}% Confidence
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
