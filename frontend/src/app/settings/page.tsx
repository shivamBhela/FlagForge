"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { Users, UserPlus, Shield, AlertCircle, Building2 } from "lucide-react";

export default function SettingsPage() {
  const { currentOrg, user } = useAuth();
  const [members, setMembers] = useState<any[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("DEVELOPER");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadMembers = async () => {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const data = await api.organizations.listMembers(currentOrg.id);
      setMembers(data);
    } catch (err: any) {
      setError(err.message || "Failed to load organization members.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMembers();
  }, [currentOrg]);

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      await api.organizations.addMember(currentOrg.id, {
        email: inviteEmail.trim(),
        role: inviteRole,
      });
      setSuccess(`Member ${inviteEmail} added successfully!`);
      setInviteEmail("");
      await loadMembers();
    } catch (err: any) {
      setError(err.message || "Failed to add member.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Title */}
      <div className="pb-4 border-b border-[#1e293b]">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Building2 className="w-5 h-5 text-blue-400" />
          <span>Organization Settings & Team Members</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Manage tenant membership, role-based access control, and organization metadata.
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center gap-2 text-rose-400 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs">
          {success}
        </div>
      )}

      {/* Organization Details Card */}
      <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b]">
        <h2 className="text-sm font-semibold text-white mb-4">Organization Profile</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3.5 rounded-lg bg-[#151e2e] border border-[#1e293b]">
            <p className="text-slate-400 text-[11px]">Organization Name</p>
            <p className="text-white font-medium mt-1">{currentOrg?.name || "None"}</p>
          </div>
          <div className="p-3.5 rounded-lg bg-[#151e2e] border border-[#1e293b]">
            <p className="text-slate-400 text-[11px]">Tenant Slug</p>
            <p className="text-white font-mono mt-1">{currentOrg?.slug || "None"}</p>
          </div>
          <div className="p-3.5 rounded-lg bg-[#151e2e] border border-[#1e293b]">
            <p className="text-slate-400 text-[11px]">Your Membership Role</p>
            <p className="text-blue-400 font-semibold mt-1">{currentOrg?.role || "VIEWER"}</p>
          </div>
        </div>
      </div>

      {/* Team Members & RBAC Card */}
      <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-[#1e293b]">
          <div>
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-400" />
              <span>Team Members ({members.length})</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Configured roles: Owner, Admin, Developer, Viewer.
            </p>
          </div>
        </div>

        {/* Members Roster Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#1e293b] text-slate-400">
                <th className="py-2 font-medium">User</th>
                <th className="py-2 font-medium">Email</th>
                <th className="py-2 font-medium">Role</th>
                <th className="py-2 font-medium">Joined Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]/60">
              {members.map((m) => (
                <tr key={m.id} className="py-3">
                  <td className="py-3 font-medium text-white flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-blue-600/30 border border-blue-500/40 flex items-center justify-center text-[10px] text-blue-300">
                      {m.full_name ? m.full_name.slice(0, 2).toUpperCase() : "U"}
                    </div>
                    <span>{m.full_name || "Unnamed"}</span>
                  </td>
                  <td className="py-3 font-mono text-slate-300">{m.email}</td>
                  <td className="py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        m.role === "OWNER"
                          ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
                          : m.role === "ADMIN"
                          ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                          : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      }`}
                    >
                      {m.role}
                    </span>
                  </td>
                  <td className="py-3 text-slate-400 text-[11px]">
                    {new Date(m.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Add Member Form */}
        <div className="pt-6 border-t border-[#1e293b]">
          <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-2">
            <UserPlus className="w-3.5 h-3.5 text-blue-400" />
            <span>Add Member by Email</span>
          </h3>
          <form onSubmit={handleAddMember} className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <input
              type="email"
              required
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="colleague@company.com"
              className="md:col-span-2 bg-[#151e2e] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="bg-[#151e2e] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="DEVELOPER">DEVELOPER</option>
              <option value="ADMIN">ADMIN</option>
              <option value="VIEWER">VIEWER</option>
            </select>
            <button
              type="submit"
              disabled={submitting}
              className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center justify-center gap-1.5 transition disabled:opacity-50"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>{submitting ? "Adding..." : "Add Member"}</span>
            </button>
          </form>
          <p className="text-[11px] text-slate-500 mt-2">
            Note: The user must already have a registered FlagForge account.
          </p>
        </div>
      </div>
    </div>
  );
}
