import type { OrgAiSettings } from "../lib/api";
import type { AgentDefinition, Matter, ProviderOption, WorkPanel } from "../types";

interface WorkPanelProps {
  activePanel: WorkPanel;
  matter: Matter;
  agents: AgentDefinition[];
  selectedAgentId: string;
  onPanelChange: (panel: WorkPanel) => void;
  workPayload?: Record<string, unknown> | null;
  arenaResult?: Record<string, unknown> | null;
  orgSettings?: OrgAiSettings | null;
  telemetry?: Record<string, unknown> | null;
  providers?: ProviderOption[];
  onSaveSettings?: (patch: Partial<OrgAiSettings>) => void;
  onRefreshTelemetry?: () => void;
}

const panels: Array<{ id: WorkPanel; label: string }> = [
  { id: "tools", label: "Tools" },
  { id: "sources", label: "Sources" },
  { id: "arena", label: "Arena" },
  { id: "admin", label: "Admin" },
  { id: "agents", label: "Agents" },
  { id: "draft", label: "Draft" },
];

export function WorkPanel({
  activePanel,
  matter,
  agents,
  selectedAgentId,
  onPanelChange,
  workPayload,
  arenaResult,
  orgSettings,
  telemetry,
  providers = [],
  onSaveSettings,
  onRefreshTelemetry,
}: WorkPanelProps) {
  const selectedAgent = agents.find((a) => a.id === selectedAgentId) ?? agents[0];
  const runs = (arenaResult?.runs as Array<Record<string, unknown>>) || [];
  const ranking = (arenaResult?.ranking as Array<Record<string, unknown>>) || [];
  const daily = (telemetry?.daily as Array<Record<string, unknown>>) || [];
  const byProvider = (telemetry?.by_provider as Array<Record<string, unknown>>) || [];

  return (
    <aside className="work-panel">
      <div className="work-tabs">
        {panels.map((panel) => (
          <button
            key={panel.id}
            type="button"
            className={activePanel === panel.id ? "work-tab work-tab--active" : "work-tab"}
            onClick={() => onPanelChange(panel.id)}
          >
            {panel.label}
          </button>
        ))}
      </div>

      <div className="work-content">
        {activePanel === "tools" && (
          <>
            <h2>Work panel</h2>
            <p className="muted">Live tool / agent activity from the last assistant turn.</p>
            {workPayload ? (
              <div className="panel-card">
                <strong>{String(workPayload.title || workPayload.view || "Activity")}</strong>
                <pre className="json-block">{JSON.stringify(workPayload, null, 2)}</pre>
              </div>
            ) : (
              <div className="panel-card">
                <p>No tool payload yet. Try /summarize, Arena, or Research.</p>
              </div>
            )}
            <div className="panel-card">
              <strong>Matter</strong>
              <p>{matter.name}</p>
              <span className="tag">{matter.privilege || "ACL"}</span>
            </div>
          </>
        )}

        {activePanel === "sources" && (
          <>
            <h2>Sources & research</h2>
            <p className="muted">Allowlisted / official links. court_ready always false here.</p>
            {Array.isArray(workPayload?.results) ? (
              (workPayload!.results as Array<Record<string, string>>).map((r) => (
                <div className="panel-card" key={r.url || r.title}>
                  <strong>{r.title}</strong>
                  <p>{r.snippet || r.source}</p>
                  {r.url && (
                    <a href={r.url} target="_blank" rel="noreferrer">
                      Open
                    </a>
                  )}
                </div>
              ))
            ) : (
              <>
                <div className="panel-card">
                  <strong>BC Laws</strong>
                  <p>Official statutes — verify currency line before reliance.</p>
                  <a href="https://www.bclaws.gov.bc.ca/" target="_blank" rel="noreferrer">
                    bclaws.gov.bc.ca
                  </a>
                </div>
                <div className="panel-card">
                  <strong>CanLII BC</strong>
                  <p>Case law index — verify treatment and pinpoints.</p>
                  <a href="https://www.canlii.org/en/bc/" target="_blank" rel="noreferrer">
                    canlii.org/en/bc
                  </a>
                </div>
              </>
            )}
          </>
        )}

        {activePanel === "arena" && (
          <>
            <h2>Model arena</h2>
            <p className="muted">Side-by-side comparison · local heuristic scores (not LMSYS Elo).</p>
            {ranking.length > 0 && (
              <div className="quality-card">
                <strong>Ranking</strong>
                {ranking.map((r) => (
                  <div key={String(r.provider)}>
                    <span>{String(r.provider)}</span>
                    <b>{String(r.overall ?? "")}</b>
                  </div>
                ))}
              </div>
            )}
            {runs.map((run) => (
              <div className="panel-card" key={`${run.provider}-${run.model}`}>
                <div className="panel-card-heading">
                  <span className="verified-dot" />
                  {String(run.provider)} / {String(run.model)}
                </div>
                <p className="clamp">{String(run.content || "").slice(0, 420)}</p>
                <pre className="json-block">{JSON.stringify(run.scores || {}, null, 2)}</pre>
              </div>
            ))}
            {runs.length === 0 && (
              <div className="panel-card">
                <p>Click <strong>Arena</strong> in the slash bar to compare providers on the current prompt.</p>
              </div>
            )}
          </>
        )}

        {activePanel === "admin" && (
          <>
            <h2>Org AI admin</h2>
            <p className="muted">Quotas, provider allowlists, cost telemetry (owner/admin).</p>
            {orgSettings && (
              <div className="panel-card admin-form">
                <label>
                  Daily request quota
                  <input
                    type="number"
                    defaultValue={orgSettings.daily_request_quota}
                    onBlur={(e) =>
                      onSaveSettings?.({ daily_request_quota: Number(e.target.value) })
                    }
                  />
                </label>
                <label>
                  Monthly token budget
                  <input
                    type="number"
                    defaultValue={orgSettings.monthly_token_budget}
                    onBlur={(e) =>
                      onSaveSettings?.({ monthly_token_budget: Number(e.target.value) })
                    }
                  />
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={orgSettings.allow_external_llm}
                    onChange={(e) => onSaveSettings?.({ allow_external_llm: e.target.checked })}
                  />
                  Allow external LLM (also needs ALA_ALLOW_EXTERNAL_LLM)
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={orgSettings.allow_web_research}
                    onChange={(e) => onSaveSettings?.({ allow_web_research: e.target.checked })}
                  />
                  Allow web research (org flag)
                </label>
                <div className="provider-allowlist">
                  <strong>Allowed providers</strong>
                  {providers.map((p) => {
                    const on = orgSettings.allowed_providers.includes(p.id);
                    return (
                      <label key={p.id} className="check">
                        <input
                          type="checkbox"
                          checked={on}
                          onChange={() => {
                            const next = on
                              ? orgSettings.allowed_providers.filter((x) => x !== p.id)
                              : [...orgSettings.allowed_providers, p.id];
                            onSaveSettings?.({ allowed_providers: next });
                          }}
                        />
                        {p.name}
                      </label>
                    );
                  })}
                </div>
                <label>
                  Default provider
                  <select
                    value={orgSettings.default_provider}
                    onChange={(e) => onSaveSettings?.({ default_provider: e.target.value })}
                  >
                    {orgSettings.allowed_providers.map((id) => (
                      <option key={id} value={id}>
                        {id}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            )}
            <div className="panel-title-row">
              <h3>Telemetry</h3>
              <button type="button" onClick={onRefreshTelemetry}>
                Refresh
              </button>
            </div>
            {byProvider.length > 0 && (
              <div className="quality-card">
                <strong>By provider</strong>
                {byProvider.map((r) => (
                  <div key={String(r.provider)}>
                    <span>
                      {String(r.provider)} · n={String(r.n)}
                    </span>
                    <b>${Number(r.cost || 0).toFixed(4)}</b>
                  </div>
                ))}
              </div>
            )}
            {daily.slice(0, 7).map((d) => (
              <div className="panel-card" key={String(d.day)}>
                <strong>{String(d.day)}</strong>
                <p>
                  {String(d.request_count)} req · in {String(d.input_tokens)} / out{" "}
                  {String(d.output_tokens)} · ${Number(d.estimated_cost_usd || 0).toFixed(4)}
                </p>
              </div>
            ))}
            {daily.length === 0 && (
              <div className="panel-card">
                <p>No usage yet. Send a chat message to record telemetry.</p>
              </div>
            )}
            {telemetry?.note && <p className="muted tiny">{String(telemetry.note)}</p>}
          </>
        )}

        {activePanel === "agents" && (
          <>
            <h2>Specialists</h2>
            {agents.map((agent) => (
              <div
                className={`panel-card ${agent.id === selectedAgent?.id ? "panel-card--active" : ""}`}
                key={agent.id}
              >
                <strong>{agent.name}</strong>
                <p>{agent.description || agent.id}</p>
              </div>
            ))}
          </>
        )}

        {activePanel === "draft" && (
          <>
            <h2>Draft</h2>
            <p className="muted">Form 66 scaffold available via API · not court-ready</p>
            <div className="draft-page">
              <small>AI DRAFT · NOT APPROVED</small>
              <h3>Form 66 Petition (scaffold)</h3>
              <p>Use GET /v1/platform/matters/{"{id}"}/drafts/form-66.docx after selecting a matter.</p>
              <div className="draft-warning">Human lawyer must verify before filing.</div>
            </div>
          </>
        )}
      </div>
    </aside>
  );
}
