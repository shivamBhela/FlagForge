"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  FolderGit2,
  Trash2,
  Layers,
  ShieldCheck,
  Plus,
  AlertCircle,
  ArrowLeft,
  KeyRound,
} from "lucide-react";
import Link from "next/link";

export default function ProjectDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { currentOrg } = useAuth();
  const projectId = params?.id as string;

  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // New environment state
  const [envName, setEnvName] = useState("");
  const [isProduction, setIsProduction] = useState(false);
  const [flagsmithKey, setFlagsmithKey] = useState("");
  const [addingEnv, setAddingEnv] = useState(false);

  const loadProject = async () => {
    if (!currentOrg || !projectId) return;
    setLoading(true);
    try {
      const data = await api.projects.get(currentOrg.id, projectId);
      setProject(data);
    } catch (err: any) {
      setError(err.message || "Failed to load project details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProject();
  }, [currentOrg, projectId]);

  const handleAddEnvironment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg || !projectId) return;
    setAddingEnv(true);
    try {
      await api.projects.createEnvironment(currentOrg.id, projectId, {
        name: envName,
        is_production: isProduction,
        flagsmith_environment_key: flagsmithKey.trim() || undefined,
      });
      setEnvName("");
      setFlagsmithKey("");
      setIsProduction(false);
      await loadProject();
    } catch (err: any) {
      setError(err.message || "Failed to create environment.");
    } finally {
      setAddingEnv(false);
    }
  };

  const handleDeleteProject = async () => {
    if (!currentOrg || !projectId) return;
    const confirmed = window.confirm(`Are you sure you want to delete "${project.name}"? This action cannot be undone.`);
    if (!confirmed) return;
    try {
      await api.projects.delete(currentOrg.id, projectId);
      router.push("/projects");
    } catch (err: any) {
      setError(err.message || "Failed to delete project.");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="flex items-center gap-3 text-slate-400 text-xs font-medium">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span>Loading project settings...</span>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-16">
        <h2 className="text-base font-semibold text-white">Project Not Found</h2>
        <p className="text-xs text-slate-400 mt-1 mb-4">The requested project could not be found or you lack permission.</p>
        <Link href="/projects" className="text-xs text-blue-400 hover:underline">
          Back to Projects
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Navigation Breadcrumb */}
      <div>
        <Link href="/projects" className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-white transition">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Projects</span>
        </Link>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center gap-2 text-rose-400 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Project Header Card */}
      <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <FolderGit2 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                {project.name}
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#151e2e] text-slate-400 border border-[#1e293b]">
                  {project.slug}
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">{project.description || "No description provided."}</p>
            </div>
          </div>
        </div>

        <button
          onClick={handleDeleteProject}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-medium border border-rose-500/30 transition self-start md:self-auto"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Delete Project</span>
        </button>
      </div>

      {/* Environments Section */}
      <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-[#1e293b]">
          <div>
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-400" />
              <span>Project Environments</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Production and non-production deployment targets linked to Flagsmith keys.
            </p>
          </div>
        </div>

        {/* Environments Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#1e293b] text-slate-400">
                <th className="py-2 font-medium">Environment</th>
                <th className="py-2 font-medium">Type</th>
                <th className="py-2 font-medium">Slug</th>
                <th className="py-2 font-medium">Flagsmith Environment Key</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]/60">
              {project.environments?.map((env: any) => (
                <tr key={env.id} className="py-3">
                  <td className="py-3 font-medium text-white flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${env.is_production ? "bg-rose-500" : "bg-emerald-500"}`} />
                    {env.name}
                  </td>
                  <td className="py-3">
                    {env.is_production ? (
                      <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px] font-semibold">
                        PRODUCTION (LOCKED)
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-semibold">
                        STAGING / DEV
                      </span>
                    )}
                  </td>
                  <td className="py-3 font-mono text-slate-400">{env.slug}</td>
                  <td className="py-3 font-mono text-slate-400 flex items-center gap-1.5">
                    <KeyRound className="w-3.5 h-3.5 text-slate-500" />
                    <span>{env.flagsmith_environment_key || "Not configured yet"}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Add Environment Sub-Form */}
        <div className="pt-6 border-t border-[#1e293b]">
          <h3 className="text-xs font-semibold text-white mb-3">Add Custom Environment</h3>
          <form onSubmit={handleAddEnvironment} className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <input
              type="text"
              required
              value={envName}
              onChange={(e) => setEnvName(e.target.value)}
              placeholder="e.g. QA Sandbox"
              className="bg-[#151e2e] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <input
              type="text"
              value={flagsmithKey}
              onChange={(e) => setFlagsmithKey(e.target.value)}
              placeholder="Flagsmith Server Key (optional)"
              className="bg-[#151e2e] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
            />
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={isProduction}
                onChange={(e) => setIsProduction(e.target.checked)}
                className="w-4 h-4 rounded bg-[#151e2e] border-[#1e293b] text-rose-600 focus:ring-0"
              />
              <span>Is Production</span>
            </label>
            <button
              type="submit"
              disabled={addingEnv}
              className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center justify-center gap-1.5 transition disabled:opacity-50"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{addingEnv ? "Adding..." : "Add Environment"}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
