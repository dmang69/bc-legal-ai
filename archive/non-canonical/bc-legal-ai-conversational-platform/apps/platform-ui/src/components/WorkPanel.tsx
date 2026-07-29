import type { AgentDefinition, Matter, WorkPanel } from "../types";

interface WorkPanelProps {
  activePanel: WorkPanel;
  matter: Matter;
  agents: AgentDefinition[];
  selectedAgentId: string;
  onPanelChange: (panel: WorkPanel) => void;
}

const panels: Array<{ id: WorkPanel; label: string }> = [
  { id: "sources", label: "Sources" },
  { id: "evidence", label: "Evidence" },
  { id: "draft", label: "Draft" },
  { id: "timeline", label: "Timeline" },
  { id: "agents", label: "Agents" },
];

export function WorkPanel({ activePanel, matter, agents, selectedAgentId, onPanelChange }: WorkPanelProps) {
  const selectedAgent = agents.find((agent) => agent.id === selectedAgentId) ?? agents[0];

  return (
    <aside className="work-panel">
      <div className="work-tabs">
        {panels.map((panel) => (
          <button
            key={panel.id}
            className={activePanel === panel.id ? "work-tab work-tab--active" : "work-tab"}
            onClick={() => onPanelChange(panel.id)}
          >
            {panel.label}
          </button>
        ))}
      </div>

      <div className="work-content">
        {activePanel === "sources" && (
          <>
            <h2>Sources</h2>
            <p className="muted">Sources used or queued for the current conversation.</p>
            <div className="panel-card">
              <div className="panel-card-heading"><span className="verified-dot" /> Synthetic Hearing Transcript</div>
              <p>Timestamped development fixture</p>
              <button>Open source</button>
            </div>
            <div className="panel-card">
              <div className="panel-card-heading"><span className="pending-dot" /> Synthetic RTB Decision</div>
              <p>Pinpoint verification pending</p>
              <button>Verify</button>
            </div>
            <div className="quality-card">
              <strong>Grounding status</strong>
              <div><span>Evidence grounded</span><b>2</b></div>
              <div><span>Verification pending</span><b>1</b></div>
              <div><span>Unsupported claims</span><b>0</b></div>
            </div>
          </>
        )}

        {activePanel === "evidence" && (
          <>
            <h2>Evidence Matrix</h2>
            <p className="muted">Matter: {matter.name}</p>
            <div className="metric-grid">
              <div><strong>12</strong><span>Documents</span></div>
              <div><strong>38</strong><span>Propositions</span></div>
              <div><strong>4</strong><span>Conflicts</span></div>
              <div><strong>7</strong><span>Gaps</span></div>
            </div>
            <div className="panel-card">
              <strong>Address amendment</strong>
              <p>Supported by transcript timestamps; legal significance requires review.</p>
              <span className="tag">Confirmed event</span>
            </div>
            <div className="panel-card">
              <strong>Property/unit attribution</strong>
              <p>Potential contradiction across records.</p>
              <span className="tag tag--warning">Unresolved conflict</span>
            </div>
          </>
        )}

        {activePanel === "draft" && (
          <>
            <div className="panel-title-row"><h2>Draft</h2><button>Open editor</button></div>
            <p className="muted">Live artifact preview</p>
            <div className="draft-page">
              <small>AI DRAFT · NOT APPROVED</small>
              <h3>Procedural Fairness</h3>
              <p>1. The record indicates that the address was amended before the tenant entered the hearing.</p>
              <p>2. The legal significance of that sequence must be assessed against the complete record and verified authorities.</p>
              <div className="draft-warning">Citation and human review required.</div>
            </div>
          </>
        )}

        {activePanel === "timeline" && (
          <>
            <h2>Chronology</h2>
            <p className="muted">Synthetic event sequence</p>
            <div className="timeline-list">
              <div><time>03:16</time><span><strong>Unit read as 990A</strong><small>Transcript</small></span></div>
              <div><time>04:36</time><span><strong>Address amendment accepted</strong><small>Transcript</small></span></div>
              <div><time>05:02</time><span><strong>Tenant joins call</strong><small>System announcement</small></span></div>
            </div>
          </>
        )}

        {activePanel === "agents" && selectedAgent && (
          <>
            <h2>Agent activity</h2>
            <div className="agent-focus">
              <span>{selectedAgent.badge}</span>
              <div><strong>{selectedAgent.name}</strong><p>{selectedAgent.description}</p></div>
            </div>
            <ol className="agent-plan">
              <li className="done">Read permitted synthetic sources</li>
              <li className="done">Extract potential issues</li>
              <li>Verify applicable authority</li>
              <li>Prepare structured work product</li>
              <li>Request human review</li>
            </ol>
            <div className="agent-controls">
              <button>Pause</button>
              <button>Edit plan</button>
              <button className="danger-button">Cancel</button>
            </div>
          </>
        )}
      </div>
    </aside>
  );
}
