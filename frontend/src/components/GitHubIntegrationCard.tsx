"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { GitBranch, Github, ShieldCheck } from "lucide-react";

export default function GitHubIntegrationCard() {
  const { currentOrg } = useAuth();
  const currentOrgId = currentOrg?.id;
  const [connection, setConnection] = useState<any>(null);
  const [repositories, setRepositories] = useState<any[]>([]);
  const [credentialType, setCredentialType] = useState("FINE_GRAINED_PAT");
  const [token, setToken] = useState("");
  const [installationId, setInstallationId] = useState("");
  const [repositoryName, setRepositoryName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    if (!currentOrg) return;
    try {
      const data = await api.github.getConnection(currentOrg.id);
      setConnection(data);
      if (data.connected) {
        const repos = await api.github.listRepositories(currentOrg.id);
        setRepositories(repos);
      } else {
        setRepositories([]);
      }
    } catch (e: any) {
      setError(e.message || "Could not load GitHub integration.");
    }
  };

  useEffect(() => {
    if (!currentOrgId) return;
    let cancelled = false;
    const orgId = currentOrgId;
    api.github.getConnection(orgId).then(async (data) => {
      if (cancelled) return;
      setConnection(data);
      if (data.connected) {
        const repos = await api.github.listRepositories(orgId);
        if (!cancelled) setRepositories(repos);
      } else {
        setRepositories([]);
      }
    }).catch((e: Error) => {
      if (!cancelled) setError(e.message || "Could not load GitHub integration.");
    });
    return () => { cancelled = true; };
  }, [currentOrgId]);

  const connect = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!currentOrg) return;
    setError(""); setMessage(""); setLoading(true);
    try {
      await api.github.connect(currentOrg.id, credentialType === "APP_INSTALLATION"
        ? { credential_type: credentialType, installation_id: installationId.trim() }
        : { credential_type: credentialType, token });
      setToken(""); setInstallationId("");
      setMessage("GitHub connection validated and stored securely.");
      await load();
    } catch (e: any) {
      setError(e.message || "GitHub connection failed.");
    } finally { setLoading(false); }
  };

  const selectRepository = async () => {
    if (!currentOrg || !repositoryName) return;
    setError(""); setLoading(true);
    try {
      const selected = await api.github.selectRepository(currentOrg.id, repositoryName);
      setConnection((current: any) => ({ ...current, ...selected }));
      setMessage(`Selected ${selected.repository_full_name} (${selected.default_branch}).`);
    } catch (e: any) {
      setError(e.message || "Repository selection failed.");
    } finally { setLoading(false); }
  };

  const disconnect = async () => {
    if (!currentOrg || !window.confirm("Disconnect GitHub from this organization? Existing pull request records will remain.")) return;
    setLoading(true); setError("");
    try { await api.github.disconnect(currentOrg.id); setMessage("GitHub disconnected."); await load(); }
    catch (e: any) { setError(e.message || "Could not disconnect GitHub."); }
    finally { setLoading(false); }
  };

  return (
    <section className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-4">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-[#151e2e] text-slate-200"><Github className="w-5 h-5" /></div>
        <div>
          <h2 className="text-sm font-bold text-white">GitHub Cleanup PRs</h2>
          <p className="text-[11px] text-slate-400">Repository access is organization-scoped. Credentials stay on the backend.</p>
        </div>
      </div>
      {error && <p role="alert" className="text-xs text-rose-300">{error}</p>}
      {message && <p role="status" className="text-xs text-emerald-300">{message}</p>}
      {connection?.connected ? (
        <div className="space-y-3">
          <p className="text-xs text-emerald-300 flex items-center gap-2"><ShieldCheck className="w-4 h-4" /> Connected with {connection.credential_type === "APP_INSTALLATION" ? "a GitHub App installation" : "a fine-grained token"}.</p>
          <div className="flex flex-col sm:flex-row gap-2">
            <select aria-label="Authorized GitHub repository" value={repositoryName || connection.repository_full_name || ""} onChange={(e) => setRepositoryName(e.target.value)} className="flex-1 px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs">
              <option value="">Select authorized repository</option>
              {repositories.map((repo) => <option key={repo.full_name} value={repo.full_name}>{repo.full_name}{repo.permissions?.push ? " (write)" : " (read only)"}</option>)}
            </select>
            <button onClick={selectRepository} disabled={!repositoryName || loading} className="px-3 py-2 rounded-lg bg-blue-600 text-xs text-white disabled:opacity-50">Save repository</button>
          </div>
          {connection.repository_full_name && <p className="text-[11px] text-slate-400 flex items-center gap-1"><GitBranch className="w-3.5 h-3.5" /> {connection.repository_full_name} · base {connection.default_branch}</p>}
          <button onClick={disconnect} disabled={loading} className="text-[11px] text-rose-300 hover:text-rose-200">Disconnect GitHub</button>
        </div>
      ) : (
        <form onSubmit={connect} className="space-y-3">
          <label className="block text-[11px] text-slate-300">Credential method
            <select value={credentialType} onChange={(e) => setCredentialType(e.target.value)} className="mt-1 w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs">
              <option value="FINE_GRAINED_PAT">Fine-grained personal access token (local alternative)</option>
              {connection?.github_app_available && <option value="APP_INSTALLATION">GitHub App installation</option>}
            </select>
          </label>
          {credentialType === "FINE_GRAINED_PAT" ? <label className="block text-[11px] text-slate-300">Fine-grained token
            <input type="password" autoComplete="new-password" required value={token} onChange={(e) => setToken(e.target.value)} className="mt-1 w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs font-mono" placeholder="Paste token; it is not saved in the browser" />
            <span className="block text-slate-500 mt-1">Grant Metadata read, Contents read/write, and Pull requests write for the intended test repository only.</span>
          </label> : <label className="block text-[11px] text-slate-300">Installed GitHub App installation ID
            <input type="text" required value={installationId} onChange={(e) => setInstallationId(e.target.value)} className="mt-1 w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs" />
            <span className="block text-slate-500 mt-1">App ID and private key must be configured on the server. The server mints short-lived installation tokens.</span>
          </label>}
          <button type="submit" disabled={loading} className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs text-white disabled:opacity-50">{loading ? "Validating…" : "Connect GitHub"}</button>
        </form>
      )}
      <p className="text-[10px] leading-4 text-slate-500">Pull requests use a separate deterministic branch, require explicit approval, and are never merged automatically.</p>
    </section>
  );
}
