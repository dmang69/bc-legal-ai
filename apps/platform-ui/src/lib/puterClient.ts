/**
 * Puter.js client for browser AI (AI base of BC Legal AI Associate).
 * Docs: https://developer.puter.com/ai/
 * API: puter.ai.chat(prompt | messages, { model, stream, ... })
 *
 * User-pays — no server API keys. Script: https://js.puter.com/v2/
 */

export const PUTER_SCRIPT_URL = "https://js.puter.com/v2/";
export const PUTER_DOCS_URL = "https://developer.puter.com/ai/";
export const DEFAULT_PUTER_MODEL =
  (import.meta.env.VITE_PUTER_MODEL as string | undefined)?.trim() || "gpt-5-nano";

/** Moonshot Kimi via Puter (https://developer.puter.com/blog/kimi-k2-5-in-puter-js/) */
export const DEFAULT_KIMI_MODEL =
  (import.meta.env.VITE_KIMI_MODEL as string | undefined)?.trim() || "moonshotai/kimi-k2.5";

export const LEGAL_PUTER_SYSTEM = [
  "You are the BC Legal AI Associate supervised workspace assistant.",
  "Be helpful, honest, and careful. Never claim to be a lawyer or give legal advice.",
  "Never mark outputs court-ready. Prefer structured answers with clear uncertainty.",
  "For BC law, direct users to verify statutes on the official BC Laws portal.",
  "Form 66 = petition; Form 67 = response to petition (BC Supreme Court JR).",
  "Do not invent case citations or statutory text. Flag when independent counsel is warranted.",
].join(" ");

export type PuterChatMessage = {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
};

type PuterAi = {
  chat: (
    promptOrMessages: string | PuterChatMessage[],
    options?: {
      model?: string;
      stream?: boolean;
      max_tokens?: number;
      temperature?: number;
    },
  ) => Promise<unknown>;
  listModels?: () => Promise<unknown>;
};

type PuterGlobal = {
  ai?: PuterAi;
};

function getPuter(): PuterGlobal | null {
  if (typeof window === "undefined") return null;
  return (window as unknown as { puter?: PuterGlobal }).puter ?? null;
}

/** True when Puter.js has loaded and puter.ai is available. */
export function isPuterReady(): boolean {
  const p = getPuter();
  return Boolean(p?.ai?.chat);
}

/** Wait briefly for the Puter script tag to initialize. */
export async function waitForPuter(timeoutMs = 8000): Promise<boolean> {
  if (isPuterReady()) return true;
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    await new Promise((r) => setTimeout(r, 100));
    if (isPuterReady()) return true;
  }
  return isPuterReady();
}

function extractText(result: unknown): string {
  if (result == null) return "";
  if (typeof result === "string") return result;
  if (typeof result !== "object") return String(result);

  const r = result as Record<string, unknown>;

  // ChatResponse shape: { message: { content: string | array } }
  const message = r.message as Record<string, unknown> | undefined;
  if (message) {
    const content = message.content;
    if (typeof content === "string") return content;
    if (Array.isArray(content)) {
      return content
        .map((part) => {
          if (typeof part === "string") return part;
          if (part && typeof part === "object") {
            const p = part as Record<string, unknown>;
            if (typeof p.text === "string") return p.text;
            if (typeof p.content === "string") return p.content;
          }
          return "";
        })
        .filter(Boolean)
        .join("");
    }
  }

  if (typeof r.text === "string") return r.text;
  if (typeof r.content === "string") return r.content;
  if (typeof r.toString === "function" && r.toString !== Object.prototype.toString) {
    const s = String(result);
    if (s && s !== "[object Object]") return s;
  }
  try {
    return JSON.stringify(result);
  } catch {
    return String(result);
  }
}

export type PuterChatResult = {
  content: string;
  model: string;
  provider: "puter";
};

/**
 * Run a multi-turn chat completion via Puter.js in the browser.
 * Users pay through their Puter account — no keys on our backend.
 */
export async function puterChat(opts: {
  messages: PuterChatMessage[];
  model?: string;
  temperature?: number;
  maxTokens?: number;
}): Promise<PuterChatResult> {
  const ready = await waitForPuter();
  if (!ready) {
    throw new Error(
      `Puter.js not loaded. Ensure <script src="${PUTER_SCRIPT_URL}"></script> is in index.html. See ${PUTER_DOCS_URL}`,
    );
  }
  const puter = getPuter()!;
  const model = opts.model?.trim() || DEFAULT_PUTER_MODEL;
  const messages = opts.messages.filter((m) => m.content?.trim());

  try {
    const result = await puter.ai!.chat(messages, {
      model,
      stream: false,
      temperature: opts.temperature,
      max_tokens: opts.maxTokens,
    });
    const content = extractText(result).trim();
    if (!content) {
      throw new Error("Puter returned an empty response.");
    }
    return { content, model, provider: "puter" };
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    throw new Error(`Puter AI failed (${model}): ${msg}`);
  }
}

/** Single-prompt helper (tests / slash tools). */
export async function puterPrompt(
  prompt: string,
  model = DEFAULT_PUTER_MODEL,
): Promise<PuterChatResult> {
  return puterChat({
    messages: [
      { role: "system", content: LEGAL_PUTER_SYSTEM },
      { role: "user", content: prompt },
    ],
    model,
  });
}

/** Kimi deep / long-context chat via Puter model moonshotai/kimi-k2.5. */
export async function kimiChat(opts: {
  messages: PuterChatMessage[];
  model?: string;
  temperature?: number;
}): Promise<PuterChatResult> {
  const result = await puterChat({
    ...opts,
    model: opts.model?.trim() || DEFAULT_KIMI_MODEL,
  });
  return { ...result, provider: "puter" };
}

/**
 * Run browser completions for Arena AI client-side providers (puter / kimi).
 * Returns rows suitable for POST /ai/arena client_runs.
 */
export async function arenaClientRuns(
  prompt: string,
  providers: string[],
  models?: Record<string, string>,
): Promise<
  Array<{ provider: string; model: string; content: string; latency_ms: number }>
> {
  const out: Array<{
    provider: string;
    model: string;
    content: string;
    latency_ms: number;
  }> = [];
  for (const pid of providers) {
    if (pid !== "puter" && pid !== "kimi") continue;
    const model =
      models?.[pid] ||
      (pid === "kimi" ? DEFAULT_KIMI_MODEL : DEFAULT_PUTER_MODEL);
    const t0 = performance.now();
    try {
      const r = await puterChat({
        messages: [
          { role: "system", content: LEGAL_PUTER_SYSTEM },
          { role: "user", content: prompt },
        ],
        model,
      });
      out.push({
        provider: pid,
        model: r.model,
        content: r.content,
        latency_ms: Math.round(performance.now() - t0),
      });
    } catch (e) {
      out.push({
        provider: pid,
        model,
        content: `Client run failed: ${e instanceof Error ? e.message : String(e)}`,
        latency_ms: Math.round(performance.now() - t0),
      });
    }
  }
  return out;
}
