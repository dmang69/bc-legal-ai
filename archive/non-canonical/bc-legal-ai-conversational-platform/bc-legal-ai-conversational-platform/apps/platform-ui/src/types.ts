export type AppMode = "public_demo" | "private";
export type ReasoningMode = "Fast" | "Balanced" | "Deep Analysis" | "Private Local";
export type WorkPanel = "sources" | "evidence" | "draft" | "timeline" | "agents";
export type MessageRole = "user" | "assistant" | "system";

export interface Matter {
  id: string;
  name: string;
  forum: string;
  fileNumber: string;
  synthetic: boolean;
  privilege: "Protected Workspace" | "General Workspace";
}

export interface Citation {
  id: string;
  title: string;
  locator: string;
  status: "verified" | "pending";
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
  citations?: Citation[];
  status?: "streaming" | "complete" | "warning";
}

export interface ChatThread {
  id: string;
  title: string;
  matterId: string;
  updatedAt: string;
  pinned?: boolean;
}

export interface AttachmentItem {
  id: string;
  name: string;
  size: number;
  type: string;
  state: "queued" | "blocked";
  reason?: string;
}

export interface AgentDefinition {
  id: string;
  name: string;
  description: string;
  badge: string;
}
