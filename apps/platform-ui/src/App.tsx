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
import { getAppMode, type AppMode } from "./lib/mode";
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
  const [token, setTok] = useState<string | null>(getToken());
  const [matters, setMatters] = useState<Array<{ matter_id: string; title: string }>>([]);
  const [msg, setMsg] = useState("");
  const [citeIn, setCiteIn] = useState("RTA s.56 retaliation");
  const [citeOut, setCiteOut] = useState("");

  useEffect(() => {
    const on = () => setOffline(false);
    const off = () => setOffline(true);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

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

  return (
    <div className="shell">
      <header className="header">
        <h1>{MODE_LABEL[mode]}</h1>
        <p className="sub">
          Family: BC Legal AI Associate · Not a lawyer · Not legal advice · Human supervision
          required
        </p>
        <p className="api-status" aria-live="polite">
          {health}
        </p>
      </header>

      {offline && (
        <div className="banner offline" role="status">
          <strong>OFFLINE</strong> — legal sources, deadlines, and matter status may be outdated.
          Reconnect before relying on or filing this material.
        </div>
      )}

      <main>
        <section className="card warn" role="note">
          <strong>M1 platform build.</strong> Auth, org/matter isolation, hash-chained audit,
          document quarantine, and fail-closed citations. Synthetic data only for demos. No
          court-ready export without privilege gates.
        </section>

        {!token ? (
          <section className="card">
            <h2>Sign in (private API)</h2>
            <form className="form" onSubmit={onLogin}>
              <label>
                Org (register only)
                <input value={orgName} onChange={(e) => setOrgName(e.target.value)} />
              </label>
              <label>
                Email
                <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
              </label>
              <label>
                Password
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  type="password"
                />
              </label>
              <div className="row">
                <button type="submit">Log in</button>
                <button type="button" onClick={onRegister}>
                  Register org
                </button>
              </div>
            </form>
          </section>
        ) : (
          <section className="card">
            <h2>Matters</h2>
            <div className="row">
              <button type="button" onClick={onNewMatter}>
                New synthetic matter
              </button>
              <button type="button" onClick={logout}>
                Log out
              </button>
            </div>
            <ul>
              {matters.map((m) => (
                <li key={m.matter_id}>
                  <code>{m.matter_id}</code> — {m.title}
                </li>
              ))}
              {matters.length === 0 && <li>No matters yet.</li>}
            </ul>
          </section>
        )}

        <section className="card">
          <h2>Citation check (fail-closed)</h2>
          <input value={citeIn} onChange={(e) => setCiteIn(e.target.value)} className="wide" />
          <button type="button" onClick={onCite}>
            Verify
          </button>
          <pre className="out">{citeOut}</pre>
        </section>

        {msg && (
          <section className="card">
            <pre className="out">{msg}</pre>
          </section>
        )}
      </main>
    </div>
  );
}
