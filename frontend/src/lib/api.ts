const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RequestOptions extends RequestInit {
  requiresAuth?: boolean;
}

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

function formatErrorDetail(detail: unknown): string | undefined {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      if (typeof item === "string") return item;
      if (!item || typeof item !== "object") return String(item);
      const issue = item as { loc?: unknown; msg?: unknown };
      const location = Array.isArray(issue.loc) ? issue.loc.filter(Boolean).join(".") : "";
      const message = typeof issue.msg === "string" ? issue.msg : "Invalid value";
      return location ? `${location}: ${message}` : message;
    });
    return messages.filter(Boolean).join("; ");
  }
  if (detail && typeof detail === "object") {
    const value = detail as { message?: unknown; error?: unknown };
    if (typeof value.message === "string") return value.message;
    if (typeof value.error === "string") return value.error;
    return JSON.stringify(detail);
  }
  return undefined;
}

export async function apiFetch<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { requiresAuth = true, headers: customHeaders, ...fetchOptions } = options;
  const headers = new Headers(customHeaders);
  headers.set("Content-Type", "application/json");

  if (requiresAuth && typeof window !== "undefined") {
    const token = localStorage.getItem("ff_access_token");
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  let data;
  try {
    data = await response.json();
  } catch (err) {
    data = null;
  }

  if (!response.ok) {
    const detail = formatErrorDetail(data?.detail) || response.statusText || "Request failed";
    throw new ApiError(response.status, detail, data);
  }

  return data as T;
}

export const api = {
  auth: {
    register: (payload: { email: string; password: string; full_name?: string }) =>
      apiFetch<any>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
        requiresAuth: false,
      }),
    login: (payload: { email: string; password: string }) =>
      apiFetch<{ access_token: string; refresh_token: string; token_type: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
        requiresAuth: false,
      }),
    me: () => apiFetch<any>("/api/v1/auth/me"),
    refresh: (refresh_token: string) =>
      apiFetch<{ access_token: string; refresh_token: string }>("/api/v1/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token }),
        requiresAuth: false,
      }),
    logout: () => apiFetch<any>("/api/v1/auth/logout", { method: "POST" }),
  },
  organizations: {
    list: () => apiFetch<any[]>("/api/v1/organizations"),
    create: (payload: { name: string; slug?: string }) =>
      apiFetch<any>("/api/v1/organizations", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    get: (orgId: string) => apiFetch<any>(`/api/v1/organizations/${orgId}`),
    listMembers: (orgId: string) => apiFetch<any[]>(`/api/v1/organizations/${orgId}/members`),
    addMember: (orgId: string, payload: { email: string; role: string }) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/members`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
  projects: {
    list: (orgId: string) => apiFetch<any[]>(`/api/v1/organizations/${orgId}/projects`),
    create: (orgId: string, payload: { name: string; slug?: string; description?: string; flagsmith_project_id?: string; create_default_environments?: boolean }) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/projects`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    get: (orgId: string, projectId: string) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/projects/${projectId}`),
    update: (orgId: string, projectId: string, payload: any) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/projects/${projectId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    delete: (orgId: string, projectId: string) =>
      apiFetch<void>(`/api/v1/organizations/${orgId}/projects/${projectId}`, {
        method: "DELETE",
      }),
    createEnvironment: (orgId: string, projectId: string, payload: { name: string; slug?: string; is_production?: boolean; flagsmith_environment_key?: string }) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/projects/${projectId}/environments`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
  flagsmith: {
    testConnection: (payload: { api_url: string; token: string; connection_type?: string }) =>
      apiFetch<{ ok: boolean; message: string; projects_count: number; latency_ms: number }>("/api/v1/flagsmith/test", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    listConnections: (orgId: string) =>
      apiFetch<any[]>(`/api/v1/flagsmith/organizations/${orgId}/flagsmith/connections`),
    createConnection: (orgId: string, payload: { name: string; api_url: string; token: string; connection_type: string; webhook_secret?: string }) =>
      apiFetch<any>(`/api/v1/flagsmith/organizations/${orgId}/flagsmith/connections`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    getConnection: (orgId: string, connId: string) =>
      apiFetch<any>(`/api/v1/flagsmith/organizations/${orgId}/flagsmith/connections/${connId}`),
    updateConnection: (orgId: string, connId: string, payload: { name?: string; api_url?: string; token?: string; connection_type?: string; webhook_secret?: string }) =>
      apiFetch<any>(`/api/v1/flagsmith/organizations/${orgId}/flagsmith/connections/${connId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    deleteConnection: (orgId: string, connId: string) =>
      apiFetch<void>(`/api/v1/flagsmith/organizations/${orgId}/flagsmith/connections/${connId}`, {
        method: "DELETE",
      }),
    testSavedConnection: (orgId: string, connId: string) =>
      apiFetch<{ ok: boolean; message: string; projects_count: number; latency_ms: number }>(
        `/api/v1/flagsmith/organizations/${orgId}/flagsmith/connections/${connId}/test`,
        { method: "POST" }
      ),
    triggerSync: (orgId: string, connId: string) =>
      apiFetch<any>(`/api/v1/flagsmith/organizations/${orgId}/flagsmith/connections/${connId}/sync`, {
        method: "POST",
      }),
    getHistory: (orgId: string, connId: string) =>
      apiFetch<any[]>(`/api/v1/flagsmith/organizations/${orgId}/flagsmith/connections/${connId}/history`),
    listFlags: (orgId: string, params?: { project_id?: string; environment_id?: string; query?: string; skip?: number; limit?: number }) => {
      const sp = new URLSearchParams();
      if (params?.project_id) sp.set("project_id", params.project_id);
      if (params?.environment_id) sp.set("environment_id", params.environment_id);
      if (params?.query) sp.set("query", params.query);
      if (params?.skip !== undefined) sp.set("skip", String(params.skip));
      if (params?.limit !== undefined) sp.set("limit", String(params.limit));
      const qs = sp.toString();
      return apiFetch<any[]>(`/api/v1/flagsmith/organizations/${orgId}/flags${qs ? `?${qs}` : ""}`);
    },
  },
  scanner: {
    listRepositories: (orgId: string) =>
      apiFetch<any[]>(`/api/v1/organizations/${orgId}/repositories`),
    createRepository: (orgId: string, payload: { name: string; repo_url: string; default_branch?: string; language?: string; project_id?: string }) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/repositories`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    triggerScan: (orgId: string, repoId: string, payload?: { commit_sha?: string; branch?: string; custom_files?: Record<string, string> }) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/repositories/${repoId}/scan`, {
        method: "POST",
        body: JSON.stringify(payload || {}),
      }),
    listScans: (orgId: string) =>
      apiFetch<any[]>(`/api/v1/organizations/${orgId}/scans`),
    listReferences: (orgId: string, flagKey?: string) =>
      apiFetch<any[]>(`/api/v1/organizations/${orgId}/flag-references${flagKey ? `?flag_key=${flagKey}` : ""}`),
  },
  dependencies: {
    getGraph: (orgId: string) =>
      apiFetch<{ nodes: any[]; edges: any[] }>(`/api/v1/organizations/${orgId}/graph`),
    getBlastRadius: (orgId: string, flagKey: string) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/graph/blast-radius?flag_key=${flagKey}`),
  },
  chaos: {
    listScenarios: (orgId: string) =>
      apiFetch<any[]>(`/api/v1/organizations/${orgId}/scenarios`),
    createScenario: (orgId: string, payload: { name: string; target_flag_key: string; description?: string; environment_name?: string; scenario_type?: string; test_traffic_rate?: number; duration_seconds?: number }) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/scenarios`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    runScenario: (orgId: string, scenarioId: string) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/scenarios/${scenarioId}/run`, {
        method: "POST",
      }),
    listRuns: (orgId: string) =>
      apiFetch<any[]>(`/api/v1/organizations/${orgId}/simulation-runs`),
  },
  telemetry: {
    getMetrics: (orgId: string, flagKey: string, environmentName?: string) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/telemetry/metrics?flag_key=${flagKey}&environment_name=${environmentName || "production"}`),
    ingestBatch: (orgId: string, items: any[]) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/telemetry/ingest`, {
        method: "POST",
        body: JSON.stringify({ items }),
      }),
  },
  guardian: {
    getPolicy: (orgId: string) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/policy`),
    updatePolicy: (orgId: string, payload: any) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/policy`, {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    evaluateRisk: (orgId: string, flagKey: string, environmentName?: string) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/guardian/evaluate?flag_key=${flagKey}&environment_name=${environmentName || "production"}`, {
        method: "POST",
      }),
    executeRollback: (orgId: string, payload: { flag_key: string; environment_name?: string; reason?: string }) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/guardian/rollback`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
  incidents: {
    listIncidents: (orgId: string) =>
      apiFetch<any[]>(`/api/v1/organizations/${orgId}/incidents`),
    listRollbackActions: (orgId: string) =>
      apiFetch<any[]>(`/api/v1/organizations/${orgId}/rollback-actions`),
    listAuditLogs: (orgId: string) =>
      apiFetch<any[]>(`/api/v1/organizations/${orgId}/audit-logs`),
    explain: (orgId: string, flagKey: string, environmentName?: string, score?: number) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/incidents/explain?flag_key=${flagKey}&environment_name=${environmentName || "production"}&score=${score || 85}`),
  },
  cleanup: {
    getStaleFlags: (orgId: string) =>
      apiFetch<any[]>(`/api/v1/organizations/${orgId}/cleanup/stale-flags`),
    generatePatch: (orgId: string, payload: { flag_key: string; file_path: string }) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/cleanup/patches/preview`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    listPatches: (orgId: string) =>
      apiFetch<any[]>(`/api/v1/organizations/${orgId}/cleanup/patches`),
    createPR: (orgId: string, patchId: string) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/cleanup/patches/${patchId}/create-pr`, {
        method: "POST",
      }),
  },
  seed: {
    seedDemo: (orgId: string) =>
      apiFetch<any>(`/api/v1/organizations/${orgId}/seed-demo`, {
        method: "POST",
      }),
  },
};
