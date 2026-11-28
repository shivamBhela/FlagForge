"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  Layers,
  Plus,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ExternalLink,
  ShieldCheck,
  Copy,
  Trash2,
  Clock,
  Zap,
  Radio,
  Server,
  Cloud,
  Check,
} from "lucide-react";
import Link from "next/link";
import GitHubIntegrationCard from "@/components/GitHubIntegrationCard";

export default function IntegrationsPage() {
  const { currentOrg, isLoading: authLoading } = useAuth();
  const [connections, setConnections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Modal & Form State
  const [showAddModal, setShowAddModal] = useState(false);
  const [connType, setConnType] = useState<"CLOUD" | "SELF_HOSTED">("SELF_HOSTED");
  const [name, setName] = useState("Flagsmith Local");
  const [apiUrl, setApiUrl] = useState("http://flagsmith:8000/api/v1");
  const [token, setToken] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string; projects_count?: number; latency_ms?: number } | null>(null);
  const [saving, setSaving] = useState(false);

  // Syncing states
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [historyConn, setHistoryConn] = useState<any | null>(null);
  const [historyList, setHistoryList] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Copy state
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const loadConnections = async () => {
    if (!currentOrg) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await api.flagsmith.listConnections(currentOrg.id);
      setConnections(data);
    } catch (err: any) {
      setError(err.message || "Failed to load Flagsmith connections.");
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
    const fetchConnections = async () => {
      setLoading(true);
      setError("");
      try {
        const connectionList = await api.flagsmith.listConnections(currentOrg.id);
        if (!ignore) setConnections(connectionList);
      } catch (loadError: any) {
        if (!ignore) setError(loadError.message || "Failed to load Flagsmith connections.");
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    void fetchConnections();
    return () => {
      ignore = true;
    };
  }, [currentOrg]);

  const handleTestConnection = async () => {
    if (!currentOrg) return;
    if (!apiUrl.trim() || !token.trim()) {
      setError("Please provide API URL and Management Token to test.");
      return;
    }
    setTesting(true);
    setTestResult(null);
    setError("");
    try {
      const res = await api.flagsmith.testConnection(currentOrg.id, {
        api_url: apiUrl.trim(),
        token: token.trim(),
        connection_type: connType,
      });
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        ok: false,
        message: err.message || "Connection verification failed.",
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    setSaving(true);
    setError("");
    try {
      await api.flagsmith.createConnection(currentOrg.id, {
        name: name.trim(),
        api_url: apiUrl.trim(),
        token: token.trim(),
        connection_type: connType,
        webhook_secret: webhookSecret.trim() || undefined,
      });
      setSuccessMsg(`Successfully connected to Flagsmith (${name})`);
      setShowAddModal(false);
      setName("Flagsmith Local");
      setToken("");
      setWebhookSecret("");
      setTestResult(null);
      await loadConnections();
    } catch (err: any) {
      setError(err.message || "Failed to create Flagsmith connection.");
    } finally {
      setSaving(false);
    }
  };

  const handleTriggerSync = async (connId: string) => {
    if (!currentOrg) return;
    setSyncingId(connId);
    setError("");
    setSuccessMsg("");
    try {
      const res = await api.flagsmith.triggerSync(currentOrg.id, connId);
      setSuccessMsg(
        `Sync completed: ${res.records_created} created, ${res.records_updated} updated, ${res.records_unchanged} unchanged.`
      );
      await loadConnections();
    } catch (err: any) {
      setError(err.message || "Synchronization failed.");
    } finally {
      setSyncingId(null);
    }
  };

  const handleDeleteConnection = async (connId: string, connName: string) => {
    if (!currentOrg) return;
    const confirmed = window.confirm(`Disconnect "${connName}"? Disconnecting will remove synced snapshots.`);
    if (!confirmed) return;
    try {
      await api.flagsmith.deleteConnection(currentOrg.id, connId);
      setSuccessMsg(`Connection "${connName}" disconnected.`);
      await loadConnections();
    } catch (err: any) {
      setError(err.message || "Failed to disconnect.");
    }
  };

  const handleViewHistory = async (conn: any) => {
    if (!currentOrg) return;
    setHistoryConn(conn);
    setLoadingHistory(true);
    try {
      const list = await api.flagsmith.getHistory(currentOrg.id, conn.id);
      setHistoryList(list);
    } catch (err: any) {
      setError(err.message || "Failed to fetch sync history.");
    } finally {
      setLoadingHistory(false);
    }
  };

  const copyWebhookUrl = (connId: string) => {
    const apiOrigin = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");
    const webhookUrl = `${apiOrigin}/api/v1/webhooks/flagsmith/${connId}`;
    navigator.clipboard.writeText(webhookUrl);
    setCopiedId(connId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="flex items-center gap-3 text-slate-400 text-xs font-medium">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span>Loading integrations...</span>
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
          Please select or create an organization to manage Flagsmith connections.
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
      <GitHubIntegrationCard />
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-400" />
            <span>Flagsmith Integrations — {currentOrg.name}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Connect Flagsmith instances, synchronize projects and feature flags, and configure real-time webhooks.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Flagsmith Connection</span>
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

      {/* Connection Cards */}
      {connections.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-[#1e293b] rounded-2xl p-8 bg-[#0c121e]">
          <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mx-auto mb-4">
            <Radio className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-white">No Flagsmith Instances Connected</h3>
          <p className="text-xs text-slate-400 mt-1 mb-6 max-w-md mx-auto">
            Connect Flagsmith Cloud or your self-hosted cluster to discover projects, synchronize feature flags, and monitor release health.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Connect Flagsmith Now</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {connections.map((conn) => {
            const isConnOk = conn.status === "CONNECTED";
            return (
              <div
                key={conn.id}
                className="p-5 rounded-xl bg-[#0c121e] border border-[#1e293b] hover:border-slate-700 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-blue-400">
                        {conn.connection_type === "CLOUD" ? <Cloud className="w-4 h-4" /> : <Server className="w-4 h-4" />}
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                          {conn.name}
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                              isConnOk
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                            }`}
                          >
                            {conn.status}
                          </span>
                        </h3>
                        <p className="text-[11px] text-slate-400 font-mono truncate max-w-[260px]">{conn.api_url}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteConnection(conn.id, conn.name)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                      title="Disconnect"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {conn.last_error && (
                    <div className="mb-3 p-2.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[11px]">
                      <strong>Error:</strong> {conn.last_error}
                    </div>
                  )}

                  <div className="space-y-2 py-2 border-y border-[#1e293b]/60 text-xs">
                    <div className="flex items-center justify-between text-slate-400">
                      <span>Credentials Encrypted</span>
                      <span className="text-emerald-400 flex items-center gap-1 font-mono text-[11px]">
                        <ShieldCheck className="w-3.5 h-3.5" /> Fernet 256-bit
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-slate-400">
                      <span>Last Synchronized</span>
                      <span className="text-slate-300 font-mono text-[11px]">
                        {conn.last_synced_at ? new Date(conn.last_synced_at).toLocaleString() : "Never"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-slate-400">
                      <span>Webhook Audit</span>
                      <span className={conn.has_webhook_secret ? "text-emerald-400" : "text-amber-400"}>
                        {conn.has_webhook_secret ? "HMAC-SHA256 Active" : "No Secret Configured"}
                      </span>
                    </div>
                  </div>

                  {/* Webhook endpoint copy */}
                  <div className="mt-3 p-2.5 rounded bg-[#151e2e] border border-[#1e293b] flex items-center justify-between gap-2">
                    <div className="truncate text-[11px] text-slate-400 font-mono">
                      <span className="text-slate-500">Webhook: </span>/api/v1/webhooks/flagsmith/{conn.id.slice(0, 8)}...
                    </div>
                    <button
                      onClick={() => copyWebhookUrl(conn.id)}
                      className="flex items-center gap-1 px-2 py-1 rounded bg-[#0c121e] hover:bg-[#1e293b] text-slate-300 text-[10px] font-medium border border-[#1e293b] transition shrink-0"
                    >
                      {copiedId === conn.id ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy URL</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                <div className="mt-5 flex items-center gap-2 pt-3 border-t border-[#1e293b]">
                  <button
                    onClick={() => handleTriggerSync(conn.id)}
                    disabled={syncingId === conn.id}
                    className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-medium text-white transition"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${syncingId === conn.id ? "animate-spin" : ""}`} />
                    <span>{syncingId === conn.id ? "Syncing..." : "Sync Now"}</span>
                  </button>

                  <button
                    onClick={() => handleViewHistory(conn)}
                    className="px-3 py-1.5 rounded-lg bg-[#151e2e] hover:bg-[#1f2937] border border-[#1e293b] text-xs font-medium text-slate-300 hover:text-white transition flex items-center gap-1"
                  >
                    <Clock className="w-3.5 h-3.5" />
                    <span>History</span>
                  </button>

                  <Link
                    href="/flags"
                    className="px-3 py-1.5 rounded-lg bg-[#151e2e] hover:bg-[#1f2937] border border-[#1e293b] text-xs font-medium text-slate-300 hover:text-white transition flex items-center gap-1"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>View Flags</span>
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Connection Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-[#0c121e] border border-[#1e293b] p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-[#1e293b]">
              <div className="flex items-center gap-2">
                <Radio className="w-5 h-5 text-blue-400" />
                <h2 className="text-base font-bold text-white">Connect Flagsmith Instance</h2>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveConnection} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">
                  Deployment Mode
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setConnType("CLOUD");
                      setApiUrl("https://api.flagsmith.com/api/v1");
                      setName("Flagsmith Cloud");
                    }}
                    className={`p-3 rounded-lg border text-left flex items-center gap-2.5 transition ${
                      connType === "CLOUD"
                        ? "bg-blue-600/10 border-blue-500 text-white"
                        : "bg-[#151e2e] border-[#1e293b] text-slate-400 hover:text-white"
                    }`}
                  >
                    <Cloud className="w-4 h-4 text-blue-400" />
                    <div>
                      <div className="text-xs font-bold">Flagsmith Cloud</div>
                      <div className="text-[10px] text-slate-400">Official Management API</div>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setConnType("SELF_HOSTED");
                      setApiUrl("http://flagsmith:8000/api/v1");
                      setName("Flagsmith Local");
                    }}
                    className={`p-3 rounded-lg border text-left flex items-center gap-2.5 transition ${
                      connType === "SELF_HOSTED"
                        ? "bg-blue-600/10 border-blue-500 text-white"
                        : "bg-[#151e2e] border-[#1e293b] text-slate-400 hover:text-white"
                    }`}
                  >
                    <Server className="w-4 h-4 text-purple-400" />
                    <div>
                      <div className="text-xs font-bold">Flagsmith Local</div>
                      <div className="text-[10px] text-slate-400">Official self-hosted deployment</div>
                    </div>
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Connection Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs focus:outline-none focus:border-blue-500"
                  placeholder="e.g. Production Cluster"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Flagsmith Management API Base URL
                </label>
                <input
                  type="url"
                  required
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs font-mono focus:outline-none focus:border-blue-500"
                  placeholder={connType === "SELF_HOSTED" ? "http://flagsmith:8000/api/v1" : "https://api.flagsmith.com/api/v1"}
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  In Docker, use the Flagsmith service name so the API can reach it on the private Compose network. Only explicitly allowlisted service hostnames bypass the private-network SSRF block; loopback and metadata addresses remain blocked.
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Flagsmith Management API Token
                </label>
                <input
                  type="password"
                  required
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs font-mono focus:outline-none focus:border-blue-500"
                  placeholder="Personal or Organization API key"
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  Encrypted at rest with Fernet symmetric keys. Never exposed in API responses or logs.
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Webhook HMAC Secret (Optional; required for signed events)
                </label>
                <input
                  type="password"
                  value={webhookSecret}
                  onChange={(e) => setWebhookSecret(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#151e2e] border border-[#1e293b] text-white text-xs font-mono focus:outline-none focus:border-blue-500"
                  placeholder="Shared secret for HMAC-SHA256 signature verification"
                />
              </div>

              {testResult && (
                <div
                  className={`p-3 rounded-lg border text-xs ${
                    testResult.ok
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : "bg-rose-500/10 border-rose-500/30 text-rose-400"
                  }`}
                >
                  <div className="font-semibold flex items-center gap-1.5">
                    {testResult.ok ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                    <span>{testResult.ok ? "Connection Validated" : "Validation Failed"}</span>
                  </div>
                  <div className="mt-1 text-[11px]">{testResult.message}</div>
                  {testResult.ok && (
                    <div className="mt-1 text-[11px] font-mono text-slate-400">
                      Discovered Projects: {testResult.projects_count} | Latency: {testResult.latency_ms}ms
                    </div>
                  )}
                </div>
              )}

              <div className="flex items-center justify-between pt-3 border-t border-[#1e293b]">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testing}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#151e2e] hover:bg-[#1f2937] border border-[#1e293b] text-xs font-medium text-slate-300 hover:text-white transition disabled:opacity-50"
                >
                  <Zap className={`w-3.5 h-3.5 ${testing ? "animate-spin text-amber-400" : "text-amber-400"}`} />
                  <span>{testing ? "Testing..." : "Test Connection"}</span>
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-3.5 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-medium text-white transition shadow-sm"
                  >
                    {saving && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />}
                    <span>{saving ? "Saving..." : "Save Connection"}</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Sync History Modal */}
      {historyConn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-[#0c121e] border border-[#1e293b] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#1e293b]">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Clock className="w-4 h-4 text-blue-400" />
                  <span>Sync Audit Trail — {historyConn.name}</span>
                </h2>
                <p className="text-[11px] text-slate-400 font-mono mt-0.5">{historyConn.api_url}</p>
              </div>
              <button onClick={() => setHistoryConn(null)} className="text-slate-400 hover:text-white text-sm">
                ✕
              </button>
            </div>

            {loadingHistory ? (
              <div className="py-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <span>Loading audit trail...</span>
              </div>
            ) : historyList.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">No sync runs recorded yet.</div>
            ) : (
              <div className="max-h-96 overflow-y-auto space-y-2.5 pr-1">
                {historyList.map((item) => {
                  const isOk = item.status === "COMPLETED";
                  return (
                    <div
                      key={item.id}
                      className="p-3 rounded-lg bg-[#151e2e] border border-[#1e293b] text-xs flex flex-col gap-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-semibold border ${
                            isOk
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                          }`}
                        >
                          {item.status} ({item.trigger})
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono">
                          {new Date(item.started_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="grid grid-cols-4 gap-2 text-center text-[11px] bg-[#0c121e] p-2 rounded border border-[#1e293b]/60">
                        <div>
                          <div className="text-emerald-400 font-bold font-mono">{item.records_created}</div>
                          <div className="text-slate-500 text-[10px]">Created</div>
                        </div>
                        <div>
                          <div className="text-blue-400 font-bold font-mono">{item.records_updated}</div>
                          <div className="text-slate-500 text-[10px]">Updated</div>
                        </div>
                        <div>
                          <div className="text-slate-300 font-bold font-mono">{item.records_unchanged}</div>
                          <div className="text-slate-500 text-[10px]">Unchanged</div>
                        </div>
                        <div>
                          <div className="text-rose-400 font-bold font-mono">{item.records_deleted}</div>
                          <div className="text-slate-500 text-[10px]">Deleted</div>
                        </div>
                      </div>
                      {item.error_details && (
                        <div className="text-[11px] text-rose-400 font-mono bg-rose-500/10 p-2 rounded">
                          {item.error_details}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
