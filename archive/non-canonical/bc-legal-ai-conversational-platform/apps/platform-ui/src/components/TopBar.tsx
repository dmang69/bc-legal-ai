import type { AppMode, Matter, ReasoningMode } from "../types";

interface TopBarProps {
  appMode: AppMode;
  matter: Matter;
  matters: Matter[];
  reasoningMode: ReasoningMode;
  onMatterChange: (matterId: string) => void;
  onModeChange: (mode: ReasoningMode) => void;
}

const modes: ReasoningMode[] = ["Fast", "Balanced", "Deep Analysis", "Private Local"];

export function TopBar({ appMode, matter, matters, reasoningMode, onMatterChange, onModeChange }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="matter-selector-wrap">
        <label htmlFor="matter-select">Workspace</label>
        <select id="matter-select" value={matter.id} onChange={(event) => onMatterChange(event.target.value)}>
          {matters.map((item) => (
            <option value={item.id} key={item.id}>{item.name}</option>
          ))}
        </select>
        <div className="matter-subtitle">
          <span>{matter.forum}</span>
          <span>·</span>
          <span>{matter.fileNumber}</span>
        </div>
      </div>

      <div className="topbar-controls">
        <div className="mode-control">
          <label htmlFor="mode-select">Mode</label>
          <select id="mode-select" value={reasoningMode} onChange={(event) => onModeChange(event.target.value as ReasoningMode)}>
            {modes.map((mode) => <option key={mode}>{mode}</option>)}
          </select>
        </div>
        <div className={`security-chip ${appMode === "public_demo" ? "security-chip--warning" : ""}`}>
          <span className="status-dot" />
          {appMode === "public_demo" ? "Synthetic demo" : "Private environment"}
        </div>
        <button className="icon-button" aria-label="Notifications">◎</button>
        <button className="icon-button" aria-label="Settings">⚙</button>
      </div>
    </header>
  );
}
