"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { FolderGit2, AlertCircle, ArrowRight } from "lucide-react";

export default function NewProjectPage() {
  const router = useRouter();
  const { currentOrg } = useAuth();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [flagsmithProjectId, setFlagsmithProjectId] = useState("");
  const [createDefaultEnvs, setCreateDefaultEnvs] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    setError("");
    setSubmitting(true);
    try {
      const proj = await api.projects.create(currentOrg.id, {
        name,
        slug: slug.trim() || undefined,
        description,
        flagsmith_project_id: flagsmithProjectId.trim() || undefined,
        create_default_environments: createDefaultEnvs,
      });
      router.push(`/projects/${proj.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create project.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8">
      <div className="p-8 rounded-2xl bg-[#0c121e] border border-[#1e293b] shadow-xl">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[#1e293b]">
          <div className="w-10 h-10 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
            <FolderGit2 className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Create New Project</h1>
            <p className="text-xs text-slate-400">
              Scoped under organization: <span className="text-blue-400 font-medium">{currentOrg?.name}</span>
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center gap-2.5 text-rose-400 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Project Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (!slug) {
                  setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, "-"));
                }
              }}
              placeholder="e.g. Core Commerce Storefront"
              className="w-full bg-[#151e2e] border border-[#1e293b] rounded-lg px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Project Slug (Identifier)</label>
            <input
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))}
              placeholder="e.g. core-commerce-storefront"
              className="w-full bg-[#151e2e] border border-[#1e293b] rounded-lg px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Description</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Primary storefront app consuming Flagsmith checkout flags..."
              className="w-full bg-[#151e2e] border border-[#1e293b] rounded-lg px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Flagsmith Project ID (Optional)</label>
            <input
              type="text"
              value={flagsmithProjectId}
              onChange={(e) => setFlagsmithProjectId(e.target.value)}
              placeholder="e.g. 10429"
              className="w-full bg-[#151e2e] border border-[#1e293b] rounded-lg px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition font-mono"
            />
          </div>

          <div className="pt-2">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={createDefaultEnvs}
                onChange={(e) => setCreateDefaultEnvs(e.target.checked)}
                className="w-4 h-4 rounded bg-[#151e2e] border-[#1e293b] text-blue-600 focus:ring-0"
              />
              <span className="text-xs text-slate-300">
                Automatically scaffold default environments (Production, Staging, Development)
              </span>
            </label>
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs flex items-center justify-center gap-2 transition shadow-sm"
            >
              <span>{submitting ? "Creating project..." : "Create Project"}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
