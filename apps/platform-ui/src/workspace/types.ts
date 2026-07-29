export type TrustState = "verified" | "partial" | "pending" | "blocked";

export type WorkspaceMode = "general" | "matter" | "document" | "research" | "drafting" | "agent";

export type ChatMessage = {
  id: string;
  author: "user" | "assistant" | "agent" | "system";
  name: string;
  timestamp: string;
  body: string;
  evidenceStatus?: TrustState;
  legalStatus?: TrustState;
  humanStatus?: TrustState;
  privacyStatus?: TrustState;
  actions?: string[];
};

export type MatterSummary = {
  id: string;
  title: string;
  forum: string;
  fileNumber: string;
  access: string;
  privilege: string;
};

export type SourceItem = {
  id: string;
  title: string;
  detail: string;
  status: TrustState;
};

export type AgentActivity = {
  id: string;
  agent: string;
  task: string;
  status: "idle" | "running" | "waiting" | "blocked" | "complete";
  detail: string;
};

export type DraftArtifact = {
  id: string;
  title: string;
  type: string;
  status: "ai_draft" | "human_review" | "lawyer_approved" | "blocked";
  warnings: string[];
};
