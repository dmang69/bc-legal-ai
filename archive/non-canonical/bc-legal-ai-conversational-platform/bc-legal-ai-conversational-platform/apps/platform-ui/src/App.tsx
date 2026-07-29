import { useMemo, useState } from "react";
import { agents, initialMessages, initialThreads, matters } from "./data";
import { Composer } from "./components/Composer";
import { MessageList } from "./components/MessageList";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { WorkPanel } from "./components/WorkPanel";
import { getMockAssistantResponse } from "./lib/mockAssistant";
import { findSensitiveText } from "./lib/security";
import type { AppMode, AttachmentItem, ChatMessage, ReasoningMode, WorkPanel as WorkPanelType } from "./types";
import "./styles.css";

const configuredAppMode = import.meta.env.VITE_APP_MODE === "private" ? "private" : "public_demo";

export default function App() {
  const [appMode] = useState<AppMode>(configuredAppMode);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeThreadId, setActiveThreadId] = useState(initialThreads[0]?.id ?? "");
  const [threads, setThreads] = useState(initialThreads);
  const [matterId, setMatterId] = useState("synthetic-rtb");
  const [reasoningMode, setReasoningMode] = useState<ReasoningMode>("Balanced");
  const [selectedAgentId, setSelectedAgentId] = useState("associate");
  const [activePanel, setActivePanel] = useState<WorkPanelType>("sources");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [warning, setWarning] = useState<string | null>(null);

  const matter = useMemo(() => matters.find((item) => item.id === matterId) ?? matters[0]!, [matterId]);
  const selectedAgent = useMemo(() => agents.find((agent) => agent.id === selectedAgentId) ?? agents[0]!, [selectedAgentId]);

  function createNewChat() {
    const id = crypto.randomUUID();
    setThreads((current) => [{ id, title: "New conversation", matterId, updatedAt: "Now" }, ...current]);
    setActiveThreadId(id);
    setMessages([
      {
        id: crypto.randomUUID(),
        role: "system",
        content: appMode === "public_demo"
          ? "New synthetic conversation. Do not enter confidential or real matter information."
          : "New matter-restricted conversation.",
        createdAt: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        status: appMode === "public_demo" ? "warning" : "complete",
      },
    ]);
    setInput("");
    setAttachments([]);
  }

  function handleFilesSelected(files: FileList) {
    const next: AttachmentItem[] = Array.from(files).map((file) => {
      const publicDemoBlocked = appMode === "public_demo";
      return {
        id: crypto.randomUUID(),
        name: file.name,
        size: file.size,
        type: file.type,
        state: publicDemoBlocked ? "blocked" : "queued",
        reason: publicDemoBlocked ? "Uploads disabled in public demo" : undefined,
      };
    });
    setAttachments((current) => [...current, ...next]);
    if (appMode === "public_demo") {
      setWarning("File uploads are disabled in public demo mode. Use synthetic bundled fixtures only.");
    }
  }

  async function sendMessage() {
    const trimmed = input.trim();
    if (!trimmed || busy) return;

    const sensitiveFindings = appMode === "public_demo" ? findSensitiveText(trimmed) : [];
    if (sensitiveFindings.length > 0) {
      setWarning(`Message blocked in public demo: ${sensitiveFindings.join(", ")}. Use synthetic information only.`);
      return;
    }

    if (attachments.some((item) => item.state === "blocked")) {
      setWarning("Remove blocked attachments before sending.");
      return;
    }

    setWarning(null);
    const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      createdAt: now,
      status: "complete",
    };
    const pendingId = crypto.randomUUID();
    const pendingMessage: ChatMessage = {
      id: pendingId,
      role: "assistant",
      content: `${selectedAgent.name} is reviewing the request…`,
      createdAt: now,
      status: "streaming",
    };

    setMessages((current) => [...current, userMessage, pendingMessage]);
    setInput("");
    setBusy(true);

    try {
      const response = await getMockAssistantResponse(trimmed, reasoningMode, selectedAgent.name);
      setMessages((current) => current.map((message) => message.id === pendingId
        ? { ...message, content: response.content, citations: response.citations, status: "complete" }
        : message));
      setThreads((current) => current.map((thread) => thread.id === activeThreadId
        ? { ...thread, title: thread.title === "New conversation" ? trimmed.slice(0, 42) : thread.title, updatedAt: "Now" }
        : thread));
    } catch {
      setMessages((current) => current.map((message) => message.id === pendingId
        ? { ...message, content: "The assistant service could not complete this request.", status: "warning" }
        : message));
    } finally {
      setBusy(false);
      setAttachments([]);
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((value) => !value)}
        onNewChat={createNewChat}
        onSelectThread={setActiveThreadId}
      />
      <main className="main-shell">
        <TopBar
          appMode={appMode}
          matter={matter}
          matters={matters}
          reasoningMode={reasoningMode}
          onMatterChange={setMatterId}
          onModeChange={setReasoningMode}
        />
        <div className="workspace-grid">
          <section className="conversation-column">
            <div className="conversation-banner">
              <div>
                <span className="eyebrow">{matter.synthetic ? "Synthetic matter" : "Active matter"}</span>
                <h1>Conversational Legal Workspace</h1>
                <p>Evidence-linked analysis, research, drafting, agents, and procedural controls in one conversation.</p>
              </div>
              <div className="trust-stack">
                <span>◈ {matter.privilege}</span>
                <span>◈ Human review required</span>
              </div>
            </div>
            <MessageList messages={messages} />
            <Composer
              value={input}
              appMode={appMode}
              busy={busy}
              attachments={attachments}
              agents={agents}
              selectedAgentId={selectedAgentId}
              warning={warning}
              onChange={setInput}
              onAgentChange={setSelectedAgentId}
              onFilesSelected={handleFilesSelected}
              onRemoveAttachment={(id) => setAttachments((current) => current.filter((item) => item.id !== id))}
              onSend={sendMessage}
            />
          </section>
          <WorkPanel
            activePanel={activePanel}
            matter={matter}
            agents={agents}
            selectedAgentId={selectedAgentId}
            onPanelChange={setActivePanel}
          />
        </div>
      </main>
    </div>
  );
}
