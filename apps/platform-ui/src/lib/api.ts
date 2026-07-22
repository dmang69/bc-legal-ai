/** Private backend origin — never bake production secrets into the bundle. */

export function getApiBase(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (fromEnv && fromEnv.length > 0) return fromEnv.replace(/\/$/, "");
  return "http://127.0.0.1:8000";
}

export type HealthResult = {
  ok: boolean;
  status?: string;
  app_mode?: string;
  phase?: string;
  db_backend?: string;
};

export async function healthCheck(): Promise<HealthResult> {
  const base = getApiBase();
  try {
    const res = await fetch(`${base}/health`, { credentials: "omit" });
    if (!res.ok) return { ok: false };
    const data = (await res.json()) as Record<string, string>;
    return {
      ok: true,
      status: data.status,
      app_mode: data.app_mode ?? data.mode,
      phase: data.phase,
      db_backend: data.db_backend,
    };
  } catch {
    return { ok: false };
  }
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
  expires_at: string;
  user: { user_id: string; org_id: string; email: string; display_name: string; role: string };
};

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

export function listMatters(): Promise<{ matters: Array<{ matter_id: string; title: string; synthetic: boolean }> }> {
  return api("/v1/platform/matters");
}

export function createMatter(title: string): Promise<{ matter_id: string; title: string }> {
  return api("/v1/platform/matters", {
    method: "POST",
    body: JSON.stringify({ title, synthetic: true }),
  });
}

export type CitationVerification = {
  verification_id?: string;
  citation_text: string;
  status: string;
  source_id?: string | null;
  source_url?: string;
  reasons: string[];
  court_ready: boolean;
};

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

export function verifyCitation(
  citation_text: string,
  expected_topic = "",
): Promise<CitationVerification> {
  return api("/v1/platform/citations/verify", {
    method: "POST",
    body: JSON.stringify({ citation_text, expected_topic }),
    auth: false,
  });
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
