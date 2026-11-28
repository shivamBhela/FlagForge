"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { FolderGit2, Plus, Layers, ArrowUpRight, ShieldCheck, Clock } from "lucide-react";

export default function ProjectsPage() {
  const { currentOrg, isLoading: authLoading } = useAuth();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadProjects = async () => {
    if (!currentOrg) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await api.projects.list(currentOrg.id);
      setProjects(data);
    } catch (err: any) {
      setError(err.message || "Failed to load projects.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    if (!currentOrg) {
      void Promise.resolve().then(() => {
        if (!ignore) setLoading(false);
      });
      return () => {
        ignore = true;
      };
    }
    const fetchProjects = async () => {
      setLoading(true);
      setError("");
      try {
        const projectList = await api.projects.list(currentOrg.id);
        if (!ignore) setProjects(projectList);
      } catch (loadError: any) {
        if (!ignore) setError(loadError.message || "Failed to load projects.");
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    void fetchProjects();
    return () => {
      ignore = true;
    };
  }, [currentOrg]);

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="flex items-center gap-3 text-slate-400 text-xs font-medium">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span>Loading project workspace...</span>
        </div>
      </div>
    );
  }

  if (!currentOrg) {
    return (
      <div className="max-w-md mx-auto text-center py-16">
        <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 mx-auto mb-4">
          <Layers className="w-6 h-6" />
        </div>
        <h2 className="text-base font-semibold text-white">No Organization Selected</h2>
        <p className="text-xs text-slate-400 mt-1 mb-6">
          You need an active organization to manage projects and feature flags.
        </p>
        <Link
          href="/organizations/new"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Create Organization</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FolderGit2 className="w-5 h-5 text-blue-400" />
            <span>Projects — {currentOrg.name}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Scoped feature release repositories and environment configurations.
          </p>
        </div>
        <Link
          href="/projects/new"
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Project</span>
        </Link>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
          {error}
        </div>
      )}

      {/* Project Cards Grid */}
      {projects.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-[#1e293b] rounded-2xl p-8">
          <FolderGit2 className="w-10 h-10 text-slate-500 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-white">No projects found in {currentOrg.name}</h3>
          <p className="text-xs text-slate-400 mt-1 mb-5">
            Create your first project to start tracking feature flag references and rollout risks.
          </p>
          <Link
            href="/projects/new"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create First Project</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((proj) => (
            <Link
              key={proj.id}
              href={`/projects/${proj.id}`}
              className="group p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] hover:border-blue-500/50 hover:bg-[#111827] transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="text-sm font-semibold text-white group-hover:text-blue-400 transition flex items-center gap-1.5">
                    {proj.name}
                    <ArrowUpRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition" />
                  </h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1e293b] text-slate-300">
                    {proj.slug}
                  </span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2 mb-4">
                  {proj.description || "No description provided."}
                </p>
              </div>

              <div className="pt-4 border-t border-[#1e293b]/70 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-1.5 text-emerald-400">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>{proj.environments?.length || 0} Environments</span>
                </div>
                <div className="flex items-center gap-1 text-slate-500 text-[11px]">
                  <Clock className="w-3 h-3" />
                  <span>{new Date(proj.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
