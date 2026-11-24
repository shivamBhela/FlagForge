"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { Building2, AlertCircle, ArrowRight } from "lucide-react";

export default function NewOrganizationPage() {
  const router = useRouter();
  const { refreshOrganizations, setCurrentOrg } = useAuth();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const org = await api.organizations.create({
        name,
        slug: slug.trim() || undefined,
      });
      await refreshOrganizations();
      setCurrentOrg(org);
      router.push("/projects");
    } catch (err: any) {
      setError(err.message || "Failed to create organization.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto py-12">
      <div className="p-8 rounded-2xl bg-[#0c121e] border border-[#1e293b] shadow-xl">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[#1e293b]">
          <div className="w-10 h-10 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
            <Building2 className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Create New Organization</h1>
            <p className="text-xs text-slate-400">Establish a multi-tenant boundary for your projects and teams</p>
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
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Organization Name</label>
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
              placeholder="Acme Global Inc"
              className="w-full bg-[#151e2e] border border-[#1e293b] rounded-lg px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Organization Slug (URL identifier)</label>
            <input
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))}
              placeholder="acme-global"
              className="w-full bg-[#151e2e] border border-[#1e293b] rounded-lg px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition font-mono"
            />
            <p className="text-[11px] text-slate-500 mt-1">Unique tenant key used for scoping API access.</p>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs flex items-center justify-center gap-2 transition shadow-sm"
            >
              <span>{submitting ? "Creating organization..." : "Create Organization"}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
