import { FormEvent, useEffect, useState } from "react";
import {
  createMatter,
  getApiBase,
  getToken,
  healthCheck,
  listMatters,
  login,
  register,
  setToken,
  verifyCitation,
} from "./lib/api";
import { getAppMode, type AppMode } from "./lib/mode";
import { ConversationalWorkspace } from "./workspace/ConversationalWorkspace";
import "./styles.css";

const MODE_LABEL: Record<AppMode, string> = {
  workbench: "BC Legal AI Workbench",
  client: "BC Legal AI Client",
  self_rep: "Self-Represented Workbench",
  portal: "BC Legal AI Portal",
};

export function App() {
  const mode = getAppMode();
  const [health, setHealth] = useState("checking…");
  const [offline, setOffline] = useState(!navigator.onLine);
  const [email, setEmail] = useState("demo@synthetic.invalid");
  const [password, setPassword] = useState("securepass99");
  const [orgName, setOrgName] = useState("Demo Org");
  const [token, setTok] = useState<string | null>(getToken());
  const [matters, setMatters] = useState<Array<{ matter_id: string; title: string }>>([]);
  const [msg, setMsg] = useState("");
  const [citeIn, setCiteIn] = useState("RTA s.56 retaliation");
  const [citeOut, setCiteOut] = useState("");
  const [surface, setSurface] = useState<"workspace" | "platform">("workspace");

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
          ? `API OK · ${h.phase ?? ""} · db=${h.db_backend ?? "?"} · ${getApiBase()}`
          : `API unreachable · ${getApiBase()}`,
      );
    });
  }, []);

  useEffect(() => {
    if (!token) return;
    listMatters()
      .then((r) => setMatters(r.matters))
      .catch((e: Error) => setMsg(e.message));
  }, [token]);

  async function onRegister(e: FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      const s = await register({ org_name: orgName, email, password, display_name: "Demo" });
      setToken(s.token);
      setTok(s.token);
      setMsg(`Registered as ${s.user.email}`);
    } catch (err) {
      setMsg(String(err));
    }
  }

  async function onLogin(e: FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      const s = await login(email, password);
      setToken(s.token);
      setTok(s.token);
      setMsg(`Logged in as ${s.user.email}`);
    } catch (err) {
      setMsg(String(err));
    }
  }

  async function onNewMatter() {
    setMsg("");
    try {
      const m = await createMatter("Synthetic demo matter");
      setMatters((prev) => [{ matter_id: m.matter_id, title: m.title }, ...prev]);
      setMsg(`Created ${m.matter_id}`);
    } catch (err) {
      setMsg(String(err));
    }
  }

  async function onCite() {
    setCiteOut("…");
    try {
      const r = await verifyCitation(citeIn, "retaliatory_eviction");
      setCiteOut(`${r.status} · court_ready=${r.court_ready}\n${r.reasons.join("\n")}`);
    } catch (err) {
      setCiteOut(String(err));
    }
  }

  function logout() {
    setToken(null);
    setTok(null);
    setMatters([]);
  }

  return (
    <div className="shell">
      <header className="header">
        <div>
          <h1>{MODE_LABEL[mode]}</h1>
          <p className="sub">
            Family: BC Legal AI Associate · Not a lawyer · Not legal advice · Human supervision
            required
          </p>
          <p className="api-status" aria-live="polite">
            {health}
          </p>
        </div>
        <div className="surface-switch" aria-label="Application surface">
          <button
            className={surface === "workspace" ? "active" : ""}
            onClick={() => setSurface("workspace")}
            type="button"
          >
            AI Workspace
          </button>
          <button
            className={surface === "platform" ? "active" : ""}
            onClick={() => setSurface("platform")}
            type="button"
          >
            Platform Admin
          </button>
        </div>
      </header>

      {offline && (
        <div className="banner offline" role="status">
          <strong>OFFLINE</strong> — legal sources, deadlines, and matter status may be outdated.
          Reconnect before relying on or filing this material.
        </div>
      )}

      {surface === "workspace" ? (
        <ConversationalWorkspace />
      ) : (
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
      )}
    </div>
  );
}
