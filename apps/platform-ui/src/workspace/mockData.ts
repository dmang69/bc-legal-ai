import type { AgentActivity, ChatMessage, DraftArtifact, MatterSummary, SourceItem } from "./types";

export const demoMatter: MatterSummary = {
  id: "matter-synthetic-001",
  title: "Example v. Sample Housing Ltd.",
  forum: "Residential Tenancy Branch",
  fileNumber: "Synthetic File 999999999",
  access: "Matter Restricted",
  privilege: "Protected Workspace",
};

export const demoMessages: ChatMessage[] = [
  {
    id: "m1",
    author: "user",
    name: "User",
    timestamp: "09:31",
    body: "Review this synthetic RTB decision and identify potential judicial-review issues.",
  },
  {
    id: "m2",
    author: "assistant",
    name: "BC Legal Associate",
    timestamp: "09:32",
    body:
      "I found three possible review issues in the synthetic record. Two are evidence-grounded, and one requires human review before it can be advanced. I will not mark any issue court-ready until the evidence, authority, deadline, and privilege gates pass.",
    evidenceStatus: "partial",
    legalStatus: "pending",
    humanStatus: "pending",
    privacyStatus: "verified",
    actions: ["Open Analysis", "View Evidence", "Verify Authorities", "Draft Form 66"],
  },
  {
    id: "m3",
    author: "agent",
    name: "Citation Clerk",
    timestamp: "09:33",
    body:
      "Authority verification is queued. BC Laws must be checked for every statute section; CanLII/court sources must be checked for cases and pinpoints.",
    evidenceStatus: "verified",
    legalStatus: "pending",
    humanStatus: "pending",
    privacyStatus: "verified",
    actions: ["Run Citation Audit", "Open Source Registry"],
  },
];

export const demoSources: SourceItem[] = [
  {
    id: "src-1",
    title: "BC Laws — Residential Tenancy Act",
    detail: "Official statute source; current and point-in-time versions required.",
    status: "pending",
  },
  {
    id: "src-2",
    title: "Synthetic RTB Decision",
    detail: "17 pages · OCR pending · page-level citations required.",
    status: "partial",
  },
  {
    id: "src-3",
    title: "CanLII / BC Courts",
    detail: "Case-law discovery only; citation verifier required before court-ready use.",
    status: "pending",
  },
];

export const demoAgents: AgentActivity[] = [
  {
    id: "a1",
    agent: "Evidence Analyst",
    task: "Build source-linked chronology",
    status: "waiting",
    detail: "Waiting for Layer 1 OCR/provenance pipeline.",
  },
  {
    id: "a2",
    agent: "Devil’s Advocate",
    task: "Identify strongest opposing arguments",
    status: "idle",
    detail: "Ready after legal issue selection.",
  },
  {
    id: "a3",
    agent: "Privilege Sentinel",
    task: "Scan outputs before export",
    status: "blocked",
    detail: "Exports remain blocked until citation, privilege, and human-approval gates pass.",
  },
];

export const demoDrafts: DraftArtifact[] = [
  {
    id: "d1",
    title: "Form 66 Petition Scaffold",
    type: "BC Supreme Court",
    status: "blocked",
    warnings: ["No verified citation audit", "No privilege export manifest", "No human deadline confirmation"],
  },
  {
    id: "d2",
    title: "Plain-language Decision Summary",
    type: "Client communication",
    status: "ai_draft",
    warnings: ["Synthetic demo only", "Lawyer review required before client use"],
  },
];
