import type { AgentDefinition, ChatMessage, ChatThread, Matter } from "./types";

export const matters: Matter[] = [
  {
    id: "general",
    name: "General Legal Workspace",
    forum: "General",
    fileNumber: "No matter selected",
    synthetic: true,
    privilege: "General Workspace",
  },
  {
    id: "synthetic-rtb",
    name: "Alex Example v. Sample Housing Ltd.",
    forum: "Residential Tenancy Branch",
    fileNumber: "SYNTHETIC-999999999",
    synthetic: true,
    privilege: "Protected Workspace",
  },
];

export const initialThreads: ChatThread[] = [
  {
    id: "thread-1",
    title: "Review RTB decision",
    matterId: "synthetic-rtb",
    updatedAt: "Today",
    pinned: true,
  },
  {
    id: "thread-2",
    title: "Evidence contradiction analysis",
    matterId: "synthetic-rtb",
    updatedAt: "Yesterday",
  },
  {
    id: "thread-3",
    title: "General procedural question",
    matterId: "general",
    updatedAt: "Jul 18",
  },
];

export const agents: AgentDefinition[] = [
  { id: "associate", name: "BC Legal Associate", description: "General legal workflow orchestrator", badge: "AI" },
  { id: "evidence", name: "Evidence Analyst", description: "Finds support, contradictions, and gaps", badge: "EV" },
  { id: "research", name: "Research Counsel", description: "Plans and performs source-linked research", badge: "RC" },
  { id: "citation", name: "Citation Clerk", description: "Checks citations and pinpoint support", badge: "CC" },
  { id: "procedure", name: "Procedural Clerk", description: "Checks forms, service, filing, and deadlines", badge: "PC" },
  { id: "drafting", name: "Drafting Counsel", description: "Creates source-linked legal drafts", badge: "DC" },
  { id: "devil", name: "Devil's Advocate", description: "Tests weaknesses and adverse positions", badge: "DA" },
  { id: "privilege", name: "Privilege Sentinel", description: "Flags confidentiality and disclosure risks", badge: "PS" },
];

export const initialMessages: ChatMessage[] = [
  {
    id: "message-system",
    role: "system",
    content: "This is a synthetic development workspace. Do not upload confidential or real matter information.",
    createdAt: "09:00",
    status: "warning",
  },
  {
    id: "message-user",
    role: "user",
    content: "Review the synthetic RTB decision and identify possible procedural-fairness issues.",
    createdAt: "09:01",
    status: "complete",
  },
  {
    id: "message-assistant",
    role: "assistant",
    content:
      "I identified three preliminary issues for review: an address amendment before the tenant joined, no recorded recap after entry, and possible use of property-level material as unit-specific evidence. These are preliminary analytical flags, not final legal conclusions.",
    createdAt: "09:01",
    status: "complete",
    citations: [
      { id: "c1", title: "Synthetic Hearing Transcript", locator: "03:16–05:02", status: "verified" },
      { id: "c2", title: "Synthetic RTB Decision", locator: "pp. 6–8", status: "pending" },
    ],
  },
];
