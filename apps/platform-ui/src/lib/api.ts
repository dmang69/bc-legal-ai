/** Private backend API client for conversational workspace. */

export function getApiBase(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (fromEnv && fromEnv.length > 0) return fromEnv.replace(/\/$/, "");
  return "http://127.0.0.1:8000";
}

const TOKEN_KEY = "ala_token";

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
  }
  const res = await fetch(`${getApiBase()}${path}`, { ...opts, headers });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return (await res.json()) as T;
}

export type Session = {
  token: string;
  user: { user_id: string; org_id: string; email: string; display_name: string; role: string };
};

export type HealthResult = {
  ok: boolean;
  phase?: string;
  db_backend?: string;
  app_mode?: string;
};

export async function healthCheck(): Promise<HealthResult> {
  try {
    const res = await fetch(`${getApiBase()}/health`);
    if (!res.ok) return { ok: false };
    const data = (await res.json()) as Record<string, string>;
    return {
      ok: true,
      phase: data.phase,
      db_backend: data.db_backend,
      app_mode: data.app_mode,
    };
  } catch {
    return { ok: false };
  }
}

export function register(body: {
  org_name: string;
  email: string;
  password: string;
  display_name?: string;
}): Promise<Session> {
  return api("/v1/platform/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
    auth: false,
  });
}

export function login(email: string, password: string): Promise<Session> {
  return api("/v1/platform/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    auth: false,
  });
}

export type Matter = { matter_id: string; title: string; synthetic?: boolean };

export type CitationVerification = {
  citation_text: string;
  status: string;
  reasons?: string[];
  court_ready?: boolean;
};

import type { DeveloperBlueprint, ExecutiveBrief, ProductBlueprint } from "../product/types";

export type WorkspaceAnalysis = {
  message: string;
  mode: string;
  classification: {
    issues: string[];
    requires_human_review: boolean;
    court_ready: boolean;
  };
  citations: CitationVerification[];
  safety: {
    court_ready: boolean;
    legal_advice: boolean;
    blockers: string[];
  };
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

export function verifyCitation(citation_text: string, expected_topic = "", matter_id = ""): Promise<{
  status: string;
  reasons: string[];
  court_ready: boolean;
}> {
  return api("/v1/platform/citations/verify", {
    method: "POST",
    body: JSON.stringify({ citation_text, expected_topic, matter_id }),
  });
}

export function listSpecialists(): Promise<{
  specialists: { id: string; name: string }[];
}> {
  return api("/v1/platform/workspace/specialists", { auth: false });
}

export function listModes(): Promise<{ modes: { id: string; label: string }[] }> {
  return api("/v1/platform/workspace/modes", { auth: false });
}

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

export function getProductBlueprint(): Promise<ProductBlueprint> {
  return api("/v1/platform/product/blueprint", { auth: false });
}

export function getExecutiveBrief(): Promise<ExecutiveBrief> {
  return api("/v1/platform/product/executive-brief", { auth: false });
}

export function getDeveloperBlueprint(): Promise<DeveloperBlueprint> {
  return api("/v1/platform/product/developer-blueprint", { auth: false });
}
