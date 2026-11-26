"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { FileCode, GitPullRequest, RefreshCw, Sparkles } from "lucide-react";

export default function CleanupStudioPage() {
  const { currentOrg } = useAuth();
  const [staleFlags, setStaleFlags] = useState<any[]>([]);
  const [patches, setPatches] = useState<any[]>([]);
  const [github, setGithub] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [editor, setEditor] = useState<any>(null);
  const [savingPatch, setSavingPatch] = useState(false);

  const loadData = async () => {
    if (!currentOrg) { setLoading(false); return; }
    setLoading(true);
    try {
      const [stale, patchList, githubState] = await Promise.all([
        api.cleanup.getStaleFlags(currentOrg.id),
        api.cleanup.listPatches(currentOrg.id),
        api.github.getConnection(currentOrg.id),
      ]);
      setStaleFlags(stale);
      setPatches(patchList);
      setGithub(githubState);
    } catch (e: any) {
      setError(e.message || "Could not load cleanup data.");
    } finally { setLoading(false); }
  };

  useEffect(() => { void loadData(); }, [currentOrg]);

  const handleGeneratePatch = async (flagKey: string, filePath: string) => {
    if (!currentOrg) return;
    setError(""); setNotice("");
    try {
      const patch = await api.cleanup.generatePatch(currentOrg.id, { flag_key: flagKey, file_path: filePath });
      if (github?.connected && github.repository_full_name) {
        const source = await api.cleanup.getGitHubSource(currentOrg.id, patch.id);
        setEditor({ patch, source });
        setNotice(`Loaded ${source.file_path} from ${source.repository_full_name}@${source.base_branch}. Edit and review the exact file before preparing a PR.`);
      } else {
        setNotice("Draft created. Connect GitHub and select an authorized repository before loading a real source file.");
      }
      await loadData();
    } catch (e: any) { setError(e.message || "Could not prepare a source diff."); }
  };

  const preparePatch = async () => {
    if (!currentOrg || !editor) return;
    setSavingPatch(true); setError("");
    try {
      const prepared = await api.cleanup.prepareGitHubPatch(currentOrg.id, editor.patch.id, {
        base_file_sha: editor.source.base_file_sha,
        base_commit_sha: editor.source.base_commit_sha,
        replacement_content: editor.replacement,
      });
      setEditor(null);
      setNotice(`Prepared ${prepared.file_path} for ${prepared.github_repository_full_name}. Review the full diff below before creating a PR.`);
      await loadData();
    } catch (e: any) { setError(e.message || "Could not prepare the diff."); }
    finally { setSavingPatch(false); }
  };

  const createPR = async (patch: any) => {
    if (!currentOrg) return;
    const confirmed = window.confirm(`Create a pull request in ${patch.github_repository_full_name} from a separate branch? The default branch will not be modified and the PR will not be merged.`);
    if (!confirmed) return;
    setError(""); setNotice("");
    try {
      const created = await api.cleanup.createPR(currentOrg.id, patch.id);
      setNotice(`Pull request ${created.github_pr_number} created. It has not been merged.`);
      await loadData();
    } catch (e: any) { setError(e.message || "GitHub could not create the pull request."); }
  };

  const refreshPR = async (patchId: string) => {
    if (!currentOrg) return;
    setError("");
    try { await api.cleanup.refreshPR(currentOrg.id, patchId); await loadData(); }
    catch (e: any) { setError(e.message || "Could not refresh pull request status."); }
  };

  if (loading) return <div className="flex min-h-[40vh] items-center justify-center text-xs text-slate-400">Loading cleanup suggestions…</div>;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="pb-4 border-b border-[#1e293b]">
        <h1 className="text-xl font-bold text-white flex items-center gap-2"><Sparkles className="w-5 h-5 text-amber-400" />Cleanup Studio</h1>
        <p className="text-xs text-slate-400 mt-1">Candidates are static references only. Verify flag rollout and ownership before editing. GitHub PRs use a reviewed patch on a separate branch.</p>
      </div>
      {!github?.connected && <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">GitHub is not connected for this organization. Local candidates and patch drafts remain available; live repository edits require an authorized GitHub integration configured in Integrations.</p>}
      {github?.connected && !github.repository_full_name && <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">Choose the authorized repository in Integrations before preparing a source diff.</p>}
      {error && <p role="alert" className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-200">{error}</p>}
      {notice && <p role="status" className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-200">{notice}</p>}

      <section className="space-y-4">
        <h2 className="text-base font-bold text-white">Candidates ({staleFlags.length})</h2>
        {staleFlags.length === 0 ? <div className="text-center py-10 rounded-xl bg-[#0c121e] border border-[#1e293b] text-slate-500 text-xs">No static flag references were found for this organization.</div> : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {staleFlags.map((item) => <div key={item.flag_key} className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-4">
              <div className="flex items-start justify-between gap-2"><span className="font-mono text-sm font-bold text-white">{item.flag_key}</span><span className="text-[10px] text-slate-400">{item.references_count} references</span></div>
              <p className="text-xs text-slate-400">{item.reason}</p>
              <div className="text-[11px] text-slate-500">{item.files?.join(", ")}</div>
              <button onClick={() => handleGeneratePatch(item.flag_key, item.files?.[0] || "")} className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white disabled:opacity-50" disabled={!item.files?.[0]}><FileCode className="w-3.5 h-3.5" />Load actual source for review</button>
            </div>)}
          </div>
        )}
      </section>

      {editor && <section className="p-5 rounded-2xl bg-[#0c121e] border border-blue-500/40 space-y-3">
        <h2 className="text-sm font-bold text-white">Edit reviewed source — {editor.source.file_path}</h2>
        <p className="text-[11px] text-slate-400">The backend verifies the source commit and file SHA again before saving the diff. Clearing the whole file is blocked.</p>
        <textarea aria-label="Proposed source file" spellCheck={false} value={editor.replacement ?? editor.source.content} onChange={(e) => setEditor({ ...editor, replacement: e.target.value })} className="w-full min-h-[320px] p-3 rounded-lg bg-[#080d17] border border-[#1e293b] text-xs font-mono text-slate-200" />
        <div className="flex gap-2"><button onClick={preparePatch} disabled={savingPatch} className="px-4 py-2 rounded-lg bg-blue-600 text-xs text-white disabled:opacity-50">{savingPatch ? "Preparing…" : "Prepare exact diff"}</button><button onClick={() => setEditor(null)} className="px-4 py-2 rounded-lg border border-[#334155] text-xs text-slate-300">Cancel</button></div>
      </section>}

      <section className="space-y-3">
        <h2 className="text-base font-bold text-white">Patch review and PR history ({patches.length})</h2>
        {patches.map((patch) => <article key={patch.id} className="p-4 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"><div><div className="text-xs font-semibold text-white">{patch.flag_key} · {patch.file_path}</div><div className="text-[11px] text-slate-400">{patch.github_repository_full_name || "No repository diff prepared"} · {patch.status}</div></div>
            <div className="flex flex-wrap gap-2">
              {patch.diff_preview?.startsWith("--- a/") && patch.status !== "PR_CREATED" && <button onClick={() => createPR(patch)} className="flex items-center gap-1 px-3 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-xs text-white"><GitPullRequest className="w-3.5 h-3.5" />Review and create PR</button>}
              {patch.pr_url && <><a href={patch.pr_url} target="_blank" rel="noreferrer" className="px-3 py-2 rounded-lg bg-blue-700 text-xs text-white">Open PR #{patch.github_pr_number}</a><button onClick={() => refreshPR(patch.id)} className="flex items-center gap-1 px-3 py-2 rounded-lg border border-[#334155] text-xs text-slate-300"><RefreshCw className="w-3 h-3" />Refresh ({patch.github_pr_state})</button></>}
            </div>
          </div>
          <pre className="max-h-80 overflow-auto whitespace-pre-wrap p-3 rounded-lg bg-[#080d17] border border-[#1e293b] text-[11px] font-mono text-emerald-200">{patch.diff_preview}</pre>
        </article>)}
        {patches.length === 0 && <p className="text-xs text-slate-500">No cleanup drafts have been generated.</p>}
      </section>
    </div>
  );
}
