import { useEffect, useState } from "react";
import { getApiBase, healthCheck } from "./lib/api";
import { getAppMode, type AppMode } from "./lib/mode";

const MODE_LABEL: Record<AppMode, string> = {
  workbench: "BC Legal AI Workbench",
  client: "BC Legal AI Client",
  self_rep: "Self-Represented Workbench",
  portal: "BC Legal AI Portal",
};

export function App() {
  const mode = getAppMode();
  const [health, setHealth] = useState<string>("checking…");
  const [offline, setOffline] = useState(!navigator.onLine);

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
    let cancelled = false;
    healthCheck()
      .then((h) => {
        if (!cancelled) {
          setHealth(
            h.ok
              ? `API OK · ${h.app_mode ?? "development"} · ${getApiBase()}`
              : `API unreachable · ${getApiBase()}`,
          );
        }
      })
      .catch(() => {
        if (!cancelled) setHealth(`API unreachable · ${getApiBase()}`);
      });
    return () => {
      cancelled = true;
    };
  }, []);

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
          <strong>Section G scaffold.</strong> Shared React/Vite UI for Tauri 2 and PWA. Real client
          matters require private backend, MFA, and matter isolation (M1+). Public demo mode rejects
          confidential workflows.
        </section>

        <section className="card">
          <h2>Application mode</h2>
          <p>
            Active: <code>{mode}</code> — set <code>VITE_APP_MODE</code> to{" "}
            <code>workbench</code>, <code>client</code>, <code>self_rep</code>, or{" "}
            <code>portal</code>.
          </p>
          <ul>
            {mode === "workbench" && (
              <>
                <li>Lawyer tools: evidence, citations, drafting, privilege approvals (backend-gated)</li>
                <li>Windows folder connector only via approved-folder native plugin</li>
              </>
            )}
            {mode === "client" && (
              <>
                <li>Status, uploads, tasks, messaging, consent — no strategy notes or other matters</li>
              </>
            )}
            {mode === "self_rep" && (
              <>
                <li>Personal organization and official-law links only</li>
                <li>Does not create an attorney–client relationship</li>
              </>
            )}
            {mode === "portal" && (
              <>
                <li>Secure web portal / installable PWA entry</li>
              </>
            )}
          </ul>
        </section>

        <section className="card">
          <h2>Delivery targets</h2>
          <ul>
            <li>Windows: signed Setup.exe / MSI</li>
            <li>macOS: notarized DMG</li>
            <li>Android: Play AAB</li>
            <li>iOS: TestFlight / App Store IPA</li>
            <li>Browser: installable PWA</li>
          </ul>
          <p className="muted">
            See <code>docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md</code>.
          </p>
        </section>
      </main>
    </div>
  );
}
