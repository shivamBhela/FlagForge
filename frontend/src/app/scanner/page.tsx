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
  Plus,
  RefreshCw,
  GitBranch,
  X,
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

  // Modal for adding a new repository
  const [showAddModal, setShowAddModal] = useState(false);
  const [newRepoName, setNewRepoName] = useState("");
  const [newRepoUrl, setNewRepoUrl] = useState("");
  const [newRepoBranch, setNewRepoBranch] = useState("main");
  const [newRepoLang, setNewRepoLang] = useState("typescript");
  const [addingRepo, setAddingRepo] = useState(false);

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
      if (repos.length > 0) {
        setSelectedRepo((prev) => (repos.some((r: any) => r.id === prev) ? prev : repos[0].id));
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
          setSelectedRepo((prev) => (repos.some((r: any) => r.id === prev) ? prev : repos[0].id));
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

  const handleAddRepository = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    if (!newRepoName.trim() || !newRepoUrl.trim()) {
      setError("Repository name and GitHub URL are required.");
      return;
    }
    setAddingRepo(true);
    setError("");
    try {
      const repo = await api.scanner.createRepository(currentOrg.id, {
        name: newRepoName.trim(),
        repo_url: newRepoUrl.trim(),
        default_branch: newRepoBranch.trim() || "main",
        language: newRepoLang,
      });
      setShowAddModal(false);
      setNewRepoName("");
      setNewRepoUrl("");
      setNewRepoBranch("main");
      setSuccessMsg(`Repository "${repo.name}" added successfully.`);
      await loadData();
      setSelectedRepo(repo.id);
    } catch (err: any) {
      setError(err.message || "Failed to register repository.");
    } finally {
      setAddingRepo(false);
    }
  };

  const handleTriggerScan = async () => {
    if (!currentOrg) return;
    if (!selectedRepo) {
      setError("Please register or select a repository before running a scan.");
      return;
    }
    setScanning(true);
    setError("");
    setSuccessMsg("");
    try {
      const scan = await api.scanner.triggerScan(currentOrg.id, selectedRepo);
      if (scan.status === "FAILED") {
        setError(`Scan failed: ${scan.error_message || "Could not fetch or parse repository archive."}`);
      } else {
        setSuccessMsg(
          `Scan completed! Discovered ${scan.findings_count} flag references across ${scan.files_scanned} source files.`
        );
      }
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
            Language-aware AST parsing and lexical extraction discovering real Flagsmith feature-flag references.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#151e2e] hover:bg-[#1e293b] text-xs font-medium text-slate-300 border border-[#1e293b] transition"
          >
            <Plus className="w-3.5 h-3.5 text-blue-400" />
            <span>Add Repository</span>
          </button>

          <button
            onClick={handleTriggerScan}
            disabled={scanning || repositories.length === 0}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${scanning ? "animate-spin" : ""}`} />
            <span>{scanning ? "Scanning Archive..." : "Run AST Scan"}</span>
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

      {/* Repository Selector Bar */}
      <div className="p-4 rounded-xl bg-[#0c121e] border border-[#1e293b] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <FolderGit2 className="w-4 h-4 text-slate-400 shrink-0" />
          <span className="text-xs font-medium text-slate-300">Active Repository:</span>
          {repositories.length === 0 ? (
            <span className="text-xs text-amber-400 font-mono">No repositories registered yet</span>
          ) : (
            <select
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
              className="px-3 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs font-mono focus:outline-none focus:border-blue-500"
            >
              {repositories.map((repo) => (
                <option key={repo.id} value={repo.id}>
                  {repo.name} ({repo.repo_url})
                </option>
              ))}
            </select>
          )}
        </div>

        {selectedRepo && (
          <div className="text-[11px] text-slate-400 flex items-center gap-2 font-mono">
            <GitBranch className="w-3.5 h-3.5 text-blue-400" />
            <span>
              branch:{" "}
              {repositories.find((r) => r.id === selectedRepo)?.default_branch || "main"}
            </span>
          </div>
        )}
      </div>

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
          <p className="text-[11px] text-slate-500 mt-1">Safe execution with zero code execution</p>
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
            {repositories.length === 0
              ? 'No repositories registered. Click "Add Repository" to connect a GitHub repository or use the companion CLI.'
              : 'No code references discovered yet. Select a repository and click "Run AST Scan" to analyze source code.'}
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

      {/* Add Repository Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl bg-[#0c121e] border border-[#1e293b] p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#1e293b]">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FolderGit2 className="w-4 h-4 text-purple-400" />
                <span>Register Code Repository</span>
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddRepository} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Repository Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. web-storefront or api-gateway"
                  value={newRepoName}
                  onChange={(e) => setNewRepoName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs font-mono focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  GitHub URL (HTTPS only)
                </label>
                <input
                  type="url"
                  required
                  placeholder="https://github.com/organization/repo"
                  value={newRepoUrl}
                  onChange={(e) => setNewRepoUrl(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs font-mono focus:outline-none focus:border-blue-500"
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  Public repositories or private repositories authorized with GITHUB_TOKEN.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Default Branch
                  </label>
                  <input
                    type="text"
                    placeholder="main"
                    value={newRepoBranch}
                    onChange={(e) => setNewRepoBranch(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs font-mono focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Primary Language
                  </label>
                  <select
                    value={newRepoLang}
                    onChange={(e) => setNewRepoLang(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs font-mono focus:outline-none focus:border-blue-500"
                  >
                    <option value="typescript">TypeScript / JS</option>
                    <option value="python">Python</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1e293b]">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addingRepo}
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition disabled:opacity-50"
                >
                  {addingRepo ? "Registering..." : "Register Repository"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
