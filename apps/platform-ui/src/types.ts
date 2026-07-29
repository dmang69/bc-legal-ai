export type AppMode = "public_demo" | "private" | "authenticated";

export type ReasoningMode = "fast" | "balanced" | "deep" | "creative" | "private_local";

export type WorkPanel =
  | "sources"
  | "tools"
  | "arena"
  | "admin"
  | "evidence"
  | "draft"
  | "agents";

export type ChatRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  status?: "complete" | "streaming" | "warning";
  citations?: Citation[] | unknown[];
  actions?: Array<{ id: string; label: string }>;
  warnings?: string[];
  provider?: string;
  model?: string;
  toolActivity?: string[];
  workPanel?: Record<string, unknown>;
}

export interface ThreadItem {
  id: string;
  title: string;
  matterId?: string;
  updatedAt: string;
}

export interface Matter {
  id: string;
  name: string;
  synthetic?: boolean;
  privilege?: string;
  matter_id?: string;
  forum?: string;
  fileNumber?: string;
}

/** @deprecated use ThreadItem */
export type ChatThread = ThreadItem & { pinned?: boolean };

export interface AgentDefinition {
  id: string;
  name: string;
  description?: string;
  badge?: string;
}

export interface Citation {
  id: string;
  title: string;
  locator?: string;
  status?: string;
}

export interface AttachmentItem {
  id: string;
  name: string;
  size: number;
  type: string;
  state: "queued" | "blocked" | "uploaded";
  reason?: string;
}

export interface ProviderOption {
  id: string;
  name: string;
  configured: boolean;
  local?: boolean;
  models?: string[];
}
