/** Private backend API client for conversational workspace + AI suite + org admin. */

export function getApiBase(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (fromEnv && fromEnv.length > 0) return fromEnv.replace(/\/$/, "");
  // Vite dev proxy
  if (import.meta.env.DEV) return "";
  return "http://127.0.0.1:8000";
}

const TOKEN_KEY = "ala_token";
const CSRF_KEY = "ala_csrf";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export function getCsrf(): string | null {
  try {
    return localStorage.getItem(CSRF_KEY);
  } catch {
    return null;
  }
}

export function setCsrf(token: string | null): void {
  try {
    if (token) localStorage.setItem(CSRF_KEY, token);
    else localStorage.removeItem(CSRF_KEY);
  } catch {
    /* ignore */
  }
}

async function api<T>(
  path: string,
  opts: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  if (opts.auth !== false) {
    const t = getToken();
    if (t) headers.Authorization = `Bearer ${t}`;
    const csrf = getCsrf();
    if (csrf && opts.method && opts.method !== "GET") {
      headers["X-CSRF-Token"] = csrf;
    }
  }
  const res = await fetch(`${getApiBase()}${path}`, {
    ...opts,
    headers,
    credentials: "include",
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return (await res.json()) as T;
}

export type Session = {
  token: string;
  csrf_token?: string;
  user: {
    user_id: string;
    org_id: string;
    email: string;
    display_name: string;
    role: string;
  };
};

export type HealthResult = {
  ok: boolean;
  phase?: string;
  db_backend?: string;
  app_mode?: string;
  ocr_available?: boolean;
  session_auth?: string;
};

export async function healthCheck(): Promise<HealthResult> {
  try {
    const res = await fetch(`${getApiBase()}/health`);
    if (!res.ok) return { ok: false };
    const data = (await res.json()) as Record<string, unknown>;
    return {
      ok: true,
      phase: String(data.phase ?? ""),
      db_backend: String(data.db_backend ?? ""),
      app_mode: String(data.app_mode ?? ""),
      ocr_available: Boolean(data.ocr_available),
      session_auth: String(data.session_auth ?? ""),
    };
  } catch {
    return { ok: false };
  }
}

function storeSession(s: Session): Session {
  setToken(s.token);
  if (s.csrf_token) setCsrf(s.csrf_token);
  return s;
}

export async function register(body: {
  org_name: string;
  email: string;
  password: string;
  display_name?: string;
}): Promise<Session> {
  const s = await api<Session>("/v1/platform/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
    auth: false,
  });
  return storeSession(s);
}

export async function login(email: string, password: string): Promise<Session> {
  const s = await api<Session>("/v1/platform/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    auth: false,
  });
  return storeSession(s);
}

export async function logout(): Promise<void> {
  try {
    await api("/v1/platform/auth/logout", { method: "POST" });
  } finally {
    setToken(null);
    setCsrf(null);
  }
}

export function me(): Promise<{
  user_id: string;
  org_id: string;
  email: string;
  display_name: string;
  role: string;
}> {
  return api("/v1/platform/auth/me");
}

export type Matter = {
  matter_id: string;
  title: string;
  synthetic?: boolean;
  client_label?: string;
};

export function listMatters(): Promise<{ matters: Matter[] }> {
  return api("/v1/platform/matters");
}

export function createMatter(title: string): Promise<Matter> {
  return api("/v1/platform/matters", {
    method: "POST",
    body: JSON.stringify({ title, synthetic: true }),
  });
}

export type ProviderMeta = {
  id: string;
  name: string;
  configured: boolean;
  external_network?: boolean;
  local?: boolean;
  models?: string[];
  family?: string;
};

export function listModelProviders(): Promise<{ providers: ProviderMeta[] }> {
  return api("/v1/platform/workspace/model-providers");
}

export function chatCapabilities(): Promise<Record<string, unknown>> {
  return api("/v1/platform/chat/capabilities");
}

export function aiSuite(): Promise<Record<string, unknown>> {
  return api("/v1/platform/ai/suite");
}

export type Conversation = {
  conversation_id: string;
  title: string;
  chat_type: string;
  matter_id?: string;
  model_mode: string;
  specialist: string;
  updated_at?: string;
};

export function createConversation(body: {
  title?: string;
  chat_type?: string;
  matter_id?: string;
  model_mode?: string;
  specialist?: string;
}): Promise<Conversation> {
  return api("/v1/platform/conversations", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function listConversations(): Promise<{ conversations: Conversation[] }> {
  return api("/v1/platform/conversations");
}

export function getConversation(id: string): Promise<{
  conversation: Conversation;
  messages: Array<{
    message_id: string;
    role: string;
    content: string;
    meta?: Record<string, unknown>;
    created_at?: string;
  }>;
}> {
  return api(`/v1/platform/conversations/${id}`);
}

export function sendMessage(
  conversationId: string,
  body: {
    content: string;
    provider?: string;
    model?: string;
    temperature?: number;
  },
): Promise<{
  user_message_id: string;
  assistant_message_id: string;
  assistant: {
    role: string;
    content: string;
    meta: {
      citations?: unknown[];
      actions?: Array<{ id: string; label: string }>;
      warnings?: string[];
      work_panel?: Record<string, unknown>;
      provider?: string;
      model?: string;
      controls?: Record<string, unknown>;
      tool_activity?: string[];
    };
  };
}> {
  return api(`/v1/platform/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function summarize(text: string): Promise<{ content: string; ok: boolean }> {
  return api("/v1/platform/ai/summarize", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function arenaCompare(prompt: string, providers: string[]): Promise<{
  runs: Array<{ provider: string; model: string; content: string; scores: Record<string, number> }>;
  ranking: Array<{ provider: string; overall?: number }>;
  winner?: { provider: string; overall?: number };
}> {
  return api("/v1/platform/ai/arena", {
    method: "POST",
    body: JSON.stringify({ prompt, providers }),
  });
}

export function webResearch(query: string): Promise<{
  ok: boolean;
  live: boolean;
  results: Array<{ title: string; url: string; snippet?: string }>;
  warnings?: string[];
}> {
  return api("/v1/platform/ai/web-research", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}

export function codeAssist(code: string, mode = "complete"): Promise<{ content: string; ok: boolean }> {
  return api("/v1/platform/ai/code", {
    method: "POST",
    body: JSON.stringify({ code, mode }),
  });
}

export type OrgAiSettings = {
  org_id: string;
  allowed_providers: string[];
  default_provider: string;
  daily_request_quota: number;
  monthly_token_budget: number;
  allow_external_llm: boolean;
  allow_web_research: boolean;
};

export function getOrgAiSettings(): Promise<OrgAiSettings> {
  return api("/v1/platform/org/ai/settings");
}

export function updateOrgAiSettings(body: Partial<OrgAiSettings>): Promise<OrgAiSettings> {
  return api("/v1/platform/org/ai/settings", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function getOrgTelemetry(): Promise<{
  settings: OrgAiSettings;
  daily: Array<Record<string, unknown>>;
  by_provider: Array<Record<string, unknown>>;
  recent: Array<Record<string, unknown>>;
  note?: string;
}> {
  return api("/v1/platform/org/ai/telemetry");
}

export function checkQuota(provider: string): Promise<{
  allowed: boolean;
  reason: string;
  usage_today?: { requests?: number; remaining?: number };
}> {
  return api(`/v1/platform/org/ai/quota?provider=${encodeURIComponent(provider)}`);
}

// Legacy product blueprint (optional surfaces)
import type { DeveloperBlueprint, ExecutiveBrief, ProductBlueprint } from "../product/types";

export function getProductBlueprint(): Promise<ProductBlueprint> {
  return api("/v1/platform/product/blueprint", { auth: false });
}

export function getExecutiveBrief(): Promise<ExecutiveBrief> {
  return api("/v1/platform/product/executive-brief", { auth: false });
}

export function getDeveloperBlueprint(): Promise<DeveloperBlueprint> {
  return api("/v1/platform/product/developer-blueprint", { auth: false });
}

export function listSpecialists(): Promise<{
  specialists: { id: string; name: string }[];
}> {
  return api("/v1/platform/workspace/specialists", { auth: false });
}

export function listModes(): Promise<{ modes: { id: string; label: string; description?: string }[] }> {
  return api("/v1/platform/workspace/modes", { auth: false });
}

export type WorkspaceAnalysis = {
  message: string;
  mode: string;
  classification: {
    issues: string[];
    requires_human_review: boolean;
    court_ready: boolean;
  };
  citations: Array<{ citation_text?: string; status: string; reasons?: string[] }>;
  safety: {
    court_ready: boolean;
    legal_advice: boolean;
    blockers: string[];
  };
};

export function analyzeWorkspaceMessage(body: {
  message: string;
  mode: string;
  matter_id?: string;
}): Promise<WorkspaceAnalysis> {
  return api("/v1/platform/workspace/analyze", {
    method: "POST",
    body: JSON.stringify(body),
    auth: false,
  });
}
