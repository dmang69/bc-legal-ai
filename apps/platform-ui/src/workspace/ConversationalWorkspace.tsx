import { FormEvent, useMemo, useState } from "react";
import { analyzeWorkspaceMessage } from "../lib/api";
import { demoAgents, demoDrafts, demoMatter, demoMessages, demoSources } from "./mockData";
import type { ChatMessage, TrustState, WorkspaceMode } from "./types";

const TRUST_LABEL: Record<TrustState, string> = {
  verified: "Verified",
  partial: "Partial",
  pending: "Pending",
  blocked: "Blocked",
};

const MODES: Array<{ id: WorkspaceMode; label: string }> = [
  { id: "general", label: "General" },
  { id: "matter", label: "Matter" },
  { id: "document", label: "Document" },
  { id: "research", label: "Research" },
  { id: "drafting", label: "Drafting" },
  { id: "agent", label: "Agent" },
];

function TrustBadge({ label, state }: { label: string; state?: TrustState }) {
  if (!state) return null;
  return <span className={`trust-badge ${state}`}>{label}: {TRUST_LABEL[state]}</span>;
}

function Sidebar({ activeMode, setActiveMode }: { activeMode: WorkspaceMode; setActiveMode: (mode: WorkspaceMode) => void }) {
  const activeNav = ["Matter Chat", "Citation Check", "Safety Gates"];
  const unavailableNav = ["Search Chats", "Projects", "Calendar", "Court Packages", "Downloads", "Settings"];
  return (
    <aside className="workspace-sidebar" aria-label="Workspace navigation">
      <div className="brand-block">
        <strong>BC Legal AI</strong>
        <span>Conversational workspace</span>
      </div>
      <div className="mode-list" aria-label="Conversation modes">
        {MODES.map((mode) => (
          <button
            className={mode.id === activeMode ? "mode-pill active" : "mode-pill"}
            key={mode.id}
            onClick={() => setActiveMode(mode.id)}
            type="button"
          >
            {mode.label}
          </button>
        ))}
      </div>
      <nav aria-label="Operational modules">
        {activeNav.map((item) => <span className="nav-item status" key={item}>{item}</span>)}
        {unavailableNav.map((item) => <span className="nav-item disabled" key={item}>{item} — unavailable</span>)}
      </nav>
    </aside>
  );
}

function MatterHeader({ activeMode }: { activeMode: WorkspaceMode }) {
  return (
    <header className="conversation-header">
      <div>
        <p className="eyebrow">{activeMode.toUpperCase()} CHAT</p>
        <h2>{demoMatter.title}</h2>
        <p className="muted">{demoMatter.forum} · {demoMatter.fileNumber}</p>
      </div>
      <div className="matter-badges" aria-label="Matter access status">
        <span>{demoMatter.access}</span>
        <span>{demoMatter.privilege}</span>
      </div>
    </header>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  return (
    <article className={`message ${message.author}`}>
      <div className="message-meta">
        <strong>{message.name}</strong>
        <span>{message.timestamp}</span>
      </div>
      <p>{message.body}</p>
      <div className="trust-row">
        <TrustBadge label="Evidence" state={message.evidenceStatus} />
        <TrustBadge label="Law" state={message.legalStatus} />
        <TrustBadge label="Human" state={message.humanStatus} />
        <TrustBadge label="Privacy" state={message.privacyStatus} />
      </div>
      {message.actions && (
        <div className="action-row" aria-label="Required next gates">
          {message.actions.map((action) => <span className="action-chip" key={action}>{action}</span>)}
        </div>
      )}
    </article>
  );
}

function Composer({ onSend }: { onSend: (body: string) => void }) {
  const [draft, setDraft] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    const body = draft.trim();
    if (!body) return;
    onSend(body);
    setDraft("");
  }

  return (
    <form className="composer" onSubmit={submit}>
      <label className="sr-only" htmlFor="chat-input">Ask BC Legal AI Associate</label>
      <textarea
        id="chat-input"
        placeholder="Ask BC Legal AI Associate…"
        rows={3}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
      />
      <div className="composer-actions">
        <span className="disabled-tool">Attachments unavailable</span>
        <span className="disabled-tool">Voice/camera unavailable</span>
        <span className="disabled-tool">External tools require approval</span>
        <button type="submit">Send to safety gateway</button>
      </div>
    </form>
  );
}

function WorkPanel() {
  return (
    <aside className="work-panel" aria-label="Workspace detail panel">
      <section>
        <h3>Sources</h3>
        {demoSources.map((source) => (
          <div className="panel-item" key={source.id}>
            <strong>{source.title}</strong>
            <p>{source.detail}</p>
            <TrustBadge label="Status" state={source.status} />
          </div>
        ))}
      </section>
      <section>
        <h3>Agent activity</h3>
        {demoAgents.map((agent) => (
          <div className={`panel-item agent ${agent.status}`} key={agent.id}>
            <strong>{agent.agent}</strong>
            <p>{agent.task}</p>
            <span className="muted">{agent.status} — {agent.detail}</span>
          </div>
        ))}
      </section>
      <section>
        <h3>Draft artifacts</h3>
        {demoDrafts.map((draft) => (
          <div className={`panel-item draft ${draft.status}`} key={draft.id}>
            <strong>{draft.title}</strong>
            <p>{draft.type} · {draft.status.replace("_", " ")}</p>
            <ul>
              {draft.warnings.map((warning) => <li key={warning}>{warning}</li>)}
            </ul>
          </div>
        ))}
      </section>
    </aside>
  );
}

export function ConversationalWorkspace() {
  const [activeMode, setActiveMode] = useState<WorkspaceMode>("matter");
  const [messages, setMessages] = useState(demoMessages);

  const modeDescription = useMemo(() => {
    if (activeMode === "general") return "General chats do not automatically access confidential matters.";
    if (activeMode === "research") return "Research mode requires official-source retrieval and citation verification.";
    if (activeMode === "agent") return "Agent tasks require plan approval and cannot file, disclose, or waive privilege.";
    return "Matter-scoped chat can access only authorized matter materials and approved tools.";
  }, [activeMode]);

  async function handleSend(body: string) {
    const now = Date.now();
    const userMessage: ChatMessage = {
      id: `user-${now}`,
      author: "user",
      name: "User",
      timestamp: "now",
      body,
    };
    const pendingMessage: ChatMessage = {
      id: `assistant-${now}`,
      author: "assistant",
      name: "BC Legal Associate",
      timestamp: "now",
      body: "Checking safety, citation, and workspace routing gates…",
      evidenceStatus: "pending",
      legalStatus: "pending",
      humanStatus: "pending",
      privacyStatus: "pending",
    };
    setMessages((prev) => [...prev, userMessage, pendingMessage]);

    try {
      const analysis = await analyzeWorkspaceMessage({
        message: body,
        mode: activeMode,
        matter_id: demoMatter.id,
      });
      const citationSummary = analysis.citations.length
        ? `\n\nCitations: ${analysis.citations
            .map((citation) => `${citation.citation_text} → ${citation.status}`)
            .join("; ")}`
        : "\n\nCitations: no verified authority detected; do not rely on legal propositions until sources are supplied and checked.";
      const blockerSummary = analysis.safety.blockers.length
        ? `\n\nGuards: ${analysis.safety.blockers.join("; ")}`
        : "";
      const assistantMessage: ChatMessage = {
        ...pendingMessage,
        body: `${analysis.message}${citationSummary}${blockerSummary}`,
        evidenceStatus: analysis.classification.issues.includes("document-summary request") ? "partial" : "pending",
        legalStatus: analysis.citations.some((citation) => citation.status === "PROVISIONAL") ? "partial" : "pending",
        humanStatus: analysis.classification.requires_human_review ? "pending" : "verified",
        privacyStatus: analysis.safety.legal_advice ? "blocked" : "verified",
        actions: analysis.safety.court_ready ? [] : ["Supply Sources", "Run Citation Check", "Human Review"],
      };
      setMessages((prev) => prev.map((message) => (message.id === pendingMessage.id ? assistantMessage : message)));
    } catch (error) {
      const blockedMessage: ChatMessage = {
        ...pendingMessage,
        body: `Request blocked or backend unavailable. No legal analysis was generated. ${String(error)}`,
        evidenceStatus: "blocked",
        legalStatus: "blocked",
        humanStatus: "pending",
        privacyStatus: "blocked",
        actions: ["Check API", "Remove Identifiers", "Use Synthetic Facts"],
      };
      setMessages((prev) => prev.map((message) => (message.id === pendingMessage.id ? blockedMessage : message)));
    }
  }

  return (
    <section className="workspace-shell" aria-label="Conversational AI legal workspace">
      <Sidebar activeMode={activeMode} setActiveMode={setActiveMode} />
      <main className="conversation-panel">
        <MatterHeader activeMode={activeMode} />
        <div className="mode-notice" role="note">{modeDescription}</div>
        <div className="messages" aria-live="polite">
          {messages.map((message) => <MessageBubble key={message.id} message={message} />)}
        </div>
        <Composer onSend={handleSend} />
      </main>
      <WorkPanel />
    </section>
  );
}
