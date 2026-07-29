import type { AppMode, Matter, ProviderOption, ReasoningMode } from "../types";

interface TopBarProps {
  appMode: AppMode;
  matter: Matter;
  matters: Matter[];
  reasoningMode: ReasoningMode;
  modes: Array<{ id: string; label: string }>;
  providers: ProviderOption[];
  providerId: string;
  health: string;
  quotaLine: string;
  onMatterChange: (matterId: string) => void;
  onModeChange: (mode: ReasoningMode) => void;
  onProviderChange: (id: string) => void;
  onNewMatter: () => void;
}

export function TopBar({
  appMode,
  matter,
  matters,
  reasoningMode,
  modes,
  providers,
  providerId,
  health,
  quotaLine,
  onMatterChange,
  onModeChange,
  onProviderChange,
  onNewMatter,
}: TopBarProps) {
  return (
    <header className="topbar">
      <div className="matter-selector-wrap">
        <label htmlFor="matter-select">Matter</label>
        <select
          id="matter-select"
          value={matter.id}
          onChange={(event) => onMatterChange(event.target.value)}
        >
          <option value="">General (no matter)</option>
          {matters.map((item) => (
            <option value={item.id} key={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <div className="matter-subtitle">
          <button type="button" className="linkish" onClick={onNewMatter}>
            + Synthetic matter
          </button>
          <span>·</span>
          <span>{matter.synthetic ? "Synthetic" : "Live ACL"}</span>
        </div>
      </div>

      <div className="topbar-controls">
        <div className="mode-control">
          <label htmlFor="provider-select">Provider</label>
          <select
            id="provider-select"
            value={providerId}
            onChange={(e) => onProviderChange(e.target.value)}
          >
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
                {p.local ? " · local" : ""}
                {!p.configured ? " · setup" : ""}
              </option>
            ))}
          </select>
        </div>
        <div className="mode-control">
          <label htmlFor="mode-select">Mode</label>
          <select
            id="mode-select"
            value={reasoningMode}
            onChange={(e) => onModeChange(e.target.value as ReasoningMode)}
          >
            {modes.map((mode) => (
              <option key={mode.id} value={mode.id}>
                {mode.label}
              </option>
            ))}
          </select>
        </div>
        <div
          className={`security-chip ${appMode === "public_demo" ? "security-chip--warning" : ""}`}
          title={health}
        >
          <span className="status-dot" />
          {quotaLine || (appMode === "public_demo" ? "Synthetic demo" : "Authenticated")}
        </div>
      </div>
    </header>
  );
}
