import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  ChatMessage,
  Conversation,
  Matter,
  createConversation,
  createMatter,
  getApiBase,
  getConversation,
  getToken,
  healthCheck,
  listConversations,
  listMatters,
  listModes,
  listSpecialists,
  login,
  register,
  sendMessage,
  setToken,
} from "./lib/api";
import "./styles.css";

type WorkPanel = {
  view?: string;
  title?: string;
  plan?: string[];
  issues?: { label: string; strength: string }[];
  [k: string]: unknown;
};

export function App() {
  const [token, setTok] = useState<string | null>(getToken());
  const [health, setHealth] = useState("…");
  const [email, setEmail] = useState("demo@synthetic.invalid");
  const [password, setPassword] = useState("securepass99");
  const [orgName, setOrgName] = useState("Demo Org");
  const [authMsg, setAuthMsg] = useState("");

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeConv, setActiveConv] = useState<Conversation | null>(null);
  const [matters, setMatters] = useState<Matter[]>([]);
  const [specialists, setSpecialists] = useState<{ id: string; name: string }[]>([]);
  const [modes, setModes] = useState<{ id: string; label: string }[]>([]);
  const [mode, setMode] = useState("balanced");
  const [specialist, setSpecialist] = useState("bc_legal_associate");
  const [chatType, setChatType] = useState("general");
  const [matterId, setMatterId] = useState("");
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [showRight, setShowRight] = useState(true);
  const [work, setWork] = useState<WorkPanel | null>(null);
  const [err, setErr] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    healthCheck().then((h) => {
      setHealth(
        h.ok
          ? `API · ${h.phase ?? "ok"} · ${h.db_backend ?? "?"} · ${getApiBase()}`
          : `API offline · ${getApiBase()}`,
      );
    });
    listSpecialists()
      .then((r) => setSpecialists(r.specialists))
      .catch(() => undefined);
    listModes()
      .then((r) => setModes(r.modes))
      .catch(() => undefined);
  }, []);

  const refreshList = useCallback(async () => {
    if (!getToken()) return;
    const r = await listConversations();
    setConversations(r.conversations);
  }, []);

  useEffect(() => {
    if (!token) return;
    refreshList().catch((e: Error) => setErr(e.message));
    listMatters()
      .then((r) => setMatters(r.matters))
      .catch(() => undefined);
  }, [token, refreshList]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function openChat(id: string) {
    setErr("");
    const r = await getConversation(id);
    setActiveId(id);
    setActiveConv(r.conversation);
    setMessages(r.messages);
    const last = [...r.messages].reverse().find((m) => m.role === "assistant");
    setWork((last?.meta?.work_panel as WorkPanel) || { view: "sources", title: "Sources" });
  }

  async function onNewChat() {
    setErr("");
    try {
      const c = await createConversation({
        title: "New chat",
        chat_type: chatType,
        matter_id: chatType === "matter" && matterId ? matterId : null,
        model_mode: mode,
        specialist,
      });
      await refreshList();
      await openChat(c.conversation_id);
    } catch (e) {
      setErr(String(e));
    }
  }

  async function onSend(e?: FormEvent) {
    e?.preventDefault();
    if (!activeId || !draft.trim() || sending) return;
    setSending(true);
    setErr("");
    const text = draft.trim();
    setDraft("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    try {
      const r = await sendMessage(activeId, text);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: r.assistant.content,
          meta: r.assistant.meta,
        },
      ]);
      if (r.assistant.meta?.work_panel) {
        setWork(r.assistant.meta.work_panel as WorkPanel);
        setShowRight(true);
      }
      await refreshList();
    } catch (ex) {
      setErr(String(ex));
    } finally {
      setSending(false);
    }
  }

  async function onRegister(e: FormEvent) {
    e.preventDefault();
    setAuthMsg("");
    try {
      const s = await register({
        org_name: orgName,
        email,
        password,
        display_name: "Demo",
      });
      setToken(s.token);
      setTok(s.token);
    } catch (ex) {
      setAuthMsg(String(ex));
    }
  }

  async function onLogin(e: FormEvent) {
    e.preventDefault();
    setAuthMsg("");
    try {
      const s = await login(email, password);
      setToken(s.token);
      setTok(s.token);
    } catch (ex) {
      setAuthMsg(String(ex));
    }
  }

  function logout() {
    setToken(null);
    setTok(null);
    setConversations([]);
    setMessages([]);
    setActiveId(null);
  }

  async function ensureMatter() {
    try {
      const m = await createMatter("Synthetic demo matter");
      setMatters((prev) => [m, ...prev]);
      setMatterId(m.matter_id);
      setChatType("matter");
    } catch (e) {
      setErr(String(e));
    }
  }

  if (!token) {
    return (
      <div className="auth-gate">
        <div className="auth-card">
          <h1>BC Legal AI Associate</h1>
          <p className="sub">
            Conversational legal workspace · Not a lawyer · Not legal advice · Human supervision
            required
          </p>
          <p className="sub">{health}</p>
          <form onSubmit={onLogin}>
            <label>
              Org (register)
              <input value={orgName} onChange={(e) => setOrgName(e.target.value)} />
            </label>
            <label>
              Email
              <input value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            <div className="row">
              <button className="primary" type="submit">
                Log in
              </button>
              <button type="button" onClick={onRegister}>
                Register
              </button>
            </div>
          </form>
          {authMsg && <div className="msg">{authMsg}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className={`workspace ${showRight ? "" : "no-right"}`}>
      <header className="topbar">
        <span className="brand">BC Legal AI Associate</span>
        <span className="badge">Conversational workspace</span>
        <span className="badge">Not legal advice</span>
        <span className="spacer" />
        <span className="status">{health}</span>
        <button type="button" onClick={() => setShowRight((v) => !v)}>
          {showRight ? "Hide panel" : "Show panel"}
        </button>
        <button type="button" onClick={logout}>
          Log out
        </button>
      </header>

      <aside className="sidebar">
        <div className="nav">
          <button type="button" className="primary" onClick={onNewChat}>
            + New Chat
          </button>
          <button type="button" onClick={ensureMatter}>
            + Synthetic matter
          </button>
        </div>
        <div className="nav">
          <div style={{ fontSize: "0.75rem", color: "var(--muted)", padding: "0.25rem 0.5rem" }}>
            Chat type
          </div>
          <select value={chatType} onChange={(e) => setChatType(e.target.value)}>
            <option value="general">General Chat</option>
            <option value="matter">Matter Chat</option>
            <option value="research">Research Chat</option>
            <option value="drafting">Drafting Chat</option>
            <option value="agent">Agent Task Chat</option>
          </select>
          {chatType === "matter" && (
            <select value={matterId} onChange={(e) => setMatterId(e.target.value)}>
              <option value="">Select matter…</option>
              {matters.map((m) => (
                <option key={m.matter_id} value={m.matter_id}>
                  {m.title}
                </option>
              ))}
            </select>
          )}
        </div>
        <div className="chat-list">
          {conversations.map((c) => (
            <button
              key={c.conversation_id}
              type="button"
              className={`chat-item ${activeId === c.conversation_id ? "active" : ""}`}
              onClick={() => openChat(c.conversation_id).catch((e: Error) => setErr(e.message))}
            >
              <span className="t">{c.title || "Chat"}</span>
              <span className="m">
                {c.chat_type}
                {c.matter_id ? " · matter" : ""}
              </span>
            </button>
          ))}
          {conversations.length === 0 && (
            <p style={{ padding: "0.75rem", color: "var(--muted)", fontSize: "0.85rem" }}>
              No chats yet. Start a New Chat.
            </p>
          )}
        </div>
      </aside>

      <section className="main">
        {activeConv?.matter_id && (
          <div className="matter-banner">
            Matter restricted · {activeConv.matter_id} · Privilege-protected workspace · Access
            controlled
          </div>
        )}
        <div className="messages">
          {!activeId && (
            <div className="msg assistant">
              <div className="role">BC Legal Associate</div>
              <div className="body">
                Conversational legal operating environment (scaffold). Ask about RTB/JR structure,
                citations, deadlines, or agent plans. Not a lawyer — human supervision required for
                filing, service, and advice.
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={m.message_id || i} className={`msg ${m.role}`}>
              <div className="role">{m.role === "user" ? "You" : "Associate"}</div>
              <div className="body">{m.content}</div>
              {m.meta?.warnings && m.meta.warnings.length > 0 && (
                <div className="warnings">
                  {m.meta.warnings.map((w, j) => (
                    <div key={j}>{w}</div>
                  ))}
                </div>
              )}
              {m.meta?.tool_activity && m.meta.tool_activity.length > 0 && (
                <div className="tools">Tools: {m.meta.tool_activity.join(" · ")}</div>
              )}
              {m.meta?.actions && m.meta.actions.length > 0 && (
                <div className="actions">
                  {m.meta.actions.map((a) => (
                    <button
                      key={a.id}
                      type="button"
                      onClick={() => {
                        if (m.meta?.work_panel) {
                          setWork(m.meta.work_panel as WorkPanel);
                          setShowRight(true);
                        }
                        setDraft(a.label);
                      }}
                    >
                      {a.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        <form className="composer" onSubmit={onSend}>
          <div className="toolbar">
            <select value={mode} onChange={(e) => setMode(e.target.value)} title="Mode">
              {(modes.length ? modes : [{ id: "balanced", label: "Balanced" }]).map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
            <select
              value={specialist}
              onChange={(e) => setSpecialist(e.target.value)}
              title="Specialist"
            >
              {(specialists.length
                ? specialists
                : [{ id: "bc_legal_associate", name: "BC Legal Associate" }]
              ).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <button type="button" disabled title="Attach (next)">
              + Attach
            </button>
            <button type="button" disabled title="Voice (later)">
              Voice
            </button>
            <button type="button" disabled title="Tools (later)">
              Tools
            </button>
            <button type="button" disabled title="Agent (use chat for plan)">
              Agent
            </button>
          </div>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={
              activeId
                ? "Ask BC Legal AI Associate…"
                : "Create a New Chat first, then ask…"
            }
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
          />
          <div className="send-row">
            {err && <span style={{ color: "var(--danger)", flex: 1, fontSize: "0.85rem" }}>{err}</span>}
            <button className="primary" type="submit" disabled={!activeId || sending || !draft.trim()}>
              {sending ? "…" : "Send"}
            </button>
          </div>
          <div className="disclaimer">
            Proposes, organizes, checks, and drafts. Humans retain judgment, filing, service, and
            representation. Court-ready requires evidence, citation, privilege, and approval gates.
          </div>
        </form>
      </section>

      {showRight && (
        <aside className="work">
          <header>
            <h2>{(work?.title as string) || "Work panel"}</h2>
            <button type="button" onClick={() => setShowRight(false)}>
              ×
            </button>
          </header>
          <div className="body">
            {!work && <p className="empty">Sources, evidence, drafts, and agent activity appear here.</p>}
            {work?.view === "agent" && work.plan && (
              <>
                <p>
                  <strong>Agent plan</strong>
                </p>
                <ol>
                  {(work.plan as string[]).map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ol>
                <p className="empty">No autonomous filing, settlement, or privilege waiver.</p>
              </>
            )}
            {work?.view === "legal_issues" && work.issues && (
              <>
                <p>
                  <strong>Legal issues (scaffold)</strong>
                </p>
                <ul>
                  {(work.issues as { label: string; strength: string }[]).map((iss, i) => (
                    <li key={i}>
                      {iss.label} — <em>{iss.strength}</em>
                    </li>
                  ))}
                </ul>
              </>
            )}
            {work?.view === "deadlines" && (
              <p>
                Use the deterministic deadline service. Only <code>HUMAN_CONFIRMED</code> dates are
                definitive for clients.
              </p>
            )}
            {work?.view === "sources" && (
              <p className="empty">
                Official sources: BC Laws for statutes; CanLII for decisions. Unverified citations
                blocked from court-ready output.
              </p>
            )}
            {work &&
              !["agent", "legal_issues", "deadlines", "sources"].includes(
                String(work.view || ""),
              ) && <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(work, null, 2)}</pre>}
          </div>
        </aside>
      )}
    </div>
  );
}
