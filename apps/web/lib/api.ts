/**
 * API client for the Enterprise AI Platform backend.
 *
 * Uses cookie sessions (credentials: 'include'), NOT bearer tokens.
 * A 401 response indicates the user is not authenticated; the caller
 * is responsible for redirecting to /login.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export async function api<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const isFormData = init.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(init.body && !isFormData ? { 'Content-Type': 'application/json' } : {}),
    ...((init.headers as Record<string, string>) || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    cache: 'no-store',
    ...init,
    headers,
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === 'string') detail = body.detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// Typed helpers for common shapes
export interface UserPublic {
  id: number;
  email: string;
  display_name: string;
  role: string;
}

export interface Workspace {
  id: number;
  name: string;
  kind: string;
}

export interface Chat {
  id: number;
  workspace_id: number;
  title: string;
}

export interface Message {
  id: number;
  chat_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  mode: string;
  model_id: string;
}

export interface BootstrapPayload {
  user: UserPublic;
  models: { id: string; label: string; provider: string; modes: string[] }[];
  workspaces: Workspace[];
  active_workspace_id: number | null;
  chats: Chat[];
  active_chat_id: number | null;
  messages: Message[];
  prompts: { id: number; title: string; body: string; scope: string }[];
  settings: Record<string, unknown>;
}

export const auth = {
  register: (body: { email: string; password: string; display_name: string; bootstrap_token?: string }) =>
    api<UserPublic>('/api/auth/register', { method: 'POST', body: JSON.stringify(body) }),
  login: (body: { email: string; password: string }) =>
    api<UserPublic>('/api/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  logout: () => api<void>('/api/auth/logout', { method: 'POST' }),
  me: () => api<UserPublic>('/api/auth/me'),
};

export const chat = {
  bootstrap: () => api<BootstrapPayload>('/api/bootstrap'),
  createWorkspace: (name: string, kind = 'general') =>
    api<Workspace>('/api/workspaces', { method: 'POST', body: JSON.stringify({ name, kind }) }),
  createChat: (workspace_id: number, title = 'New Chat') =>
    api<Chat>('/api/chats', { method: 'POST', body: JSON.stringify({ workspace_id, title }) }),
  getChat: (chatId: number) =>
    api<{ chat: Chat; messages: Message[] }>(`/api/chats/${chatId}`),
  sendMessage: (chatId: number, content: string, mode: string, model_id: string) =>
    api<{ reply: string }>(`/api/chats/${chatId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, mode, model_id }),
    }),
};
