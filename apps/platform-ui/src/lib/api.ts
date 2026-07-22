/** Private backend origin — never bake production secrets into the bundle. */

export function getApiBase(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (fromEnv && fromEnv.length > 0) return fromEnv.replace(/\/$/, "");
  // Dev default: FastAPI local
  return "http://127.0.0.1:8000";
}

export type HealthResult = {
  ok: boolean;
  status?: string;
  app_mode?: string;
  phase?: string;
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
    };
  } catch {
    return { ok: false };
  }
}
