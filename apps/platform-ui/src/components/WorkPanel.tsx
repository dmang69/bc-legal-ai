import type { FeatureOption, FeaturesManifest, OrgAiSettings } from "../lib/api";
import type { AgentDefinition, Matter, ProviderOption, WorkPanel } from "../types";

interface WorkPanelProps {
  activePanel: WorkPanel;
  matter: Matter;
  agents: AgentDefinition[];
  selectedAgentId: string;
  onPanelChange: (panel: WorkPanel) => void;
  workPayload?: Record<string, unknown> | null;
  arenaResult?: Record<string, unknown> | null;
  openClawResult?: Record<string, unknown> | null;
  featuresManifest?: FeaturesManifest | null;
  orgSettings?: OrgAiSettings | null;
  telemetry?: Record<string, unknown> | null;
  providers?: ProviderOption[];
  onSaveSettings?: (patch: Partial<OrgAiSettings>) => void;
  onRefreshTelemetry?: () => void;
  onRunOpenClaw?: () => void;
  onRunArenaPreset?: (preset: string) => void;
}

const panels: Array<{ id: WorkPanel; label: string }> = [
  { id: "tools", label: "Tools" },
  { id: "sources", label: "Sources" },
  { id: "features", label: "Features" },
  { id: "arena", label: "Arena AI" },
  { id: "openclaw", label: "OpenClaw" },
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
  openClawResult,
  featuresManifest,
  orgSettings,
  telemetry,
  providers = [],
  onSaveSettings,
  onRefreshTelemetry,
  onRunOpenClaw,
  onRunArenaPreset,
}: WorkPanelProps) {
  const selectedAgent = agents.find((a) => a.id === selectedAgentId) ?? agents[0];
  const runs = (arenaResult?.runs as Array<Record<string, unknown>>) || [];
  const ranking = (arenaResult?.ranking as Array<Record<string, unknown>>) || [];
  const daily = (telemetry?.daily as Array<Record<string, unknown>>) || [];
  const byProvider = (telemetry?.by_provider as Array<Record<string, unknown>>) || [];
  const clawSteps =
    (openClawResult?.steps as Array<Record<string, unknown>>) ||
    (workPayload?.steps as Array<Record<string, unknown>>) ||
    [];
  const clawPlan =
    (openClawResult?.plan as Array<Record<string, unknown>>) ||
    (workPayload?.plan as Array<Record<string, unknown>>) ||
    [];

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

        {activePanel === "features" && (
          <>
            <h2>Feature options</h2>
            <p className="muted">
              Structured platform capabilities — install clients, AI suite, legal tools, productivity,
              governance. Not legal advice · court_ready always false by default.
            </p>
            {(featuresManifest?.locks || []).length > 0 && (
              <div className="panel-card">
                <strong>Locks</strong>
                <p className="muted tiny">{(featuresManifest?.locks || []).join(" · ")}</p>
              </div>
            )}
            {(featuresManifest?.categories || []).map((cat) => {
              const items =
                featuresManifest?.by_category?.[cat.id] ||
                (featuresManifest?.features || []).filter((f) => f.category === cat.id);
              if (!items?.length) return null;
              return (
                <div key={cat.id} className="panel-card">
                  <strong>{cat.label}</strong>
                  {cat.description ? <p className="muted tiny">{cat.description}</p> : null}
                  <ul className="feature-options-list">
                    {items.map((f: FeatureOption) => (
                      <li key={f.id} className={f.enabled ? "feature-on" : "feature-off"}>
                        <span className="feature-name">
                          {f.enabled ? "●" : "○"} {f.name}
                        </span>
                        <span className="tag">{f.status}</span>
                        {f.org_toggleable ? <span className="tag">org</span> : null}
                        <p className="muted tiny">{f.description}</p>
                        {(f.platforms || []).length > 0 ? (
                          <p className="muted tiny">Platforms: {(f.platforms || []).join(", ")}</p>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
            {!featuresManifest?.features?.length && (
              <div className="panel-card">
                <p>Sign in to load structured feature options from the API.</p>
              </div>
            )}
            {featuresManifest?.selection_guide && (
              <div className="panel-card">
                <strong>Recommended bundles</strong>
                {Object.entries(featuresManifest.selection_guide).map(([k, ids]) => (
                  <div key={k} style={{ marginTop: 8 }}>
                    <code>{k}</code>
                    <p className="muted tiny">{(ids as string[]).join(", ")}</p>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {activePanel === "arena" && (
          <>
            <h2>Arena AI</h2>
            <p className="muted">
              Multi-model comparison · legal-aware heuristics (not LMSYS Elo) · Puter/Kimi client runs merge.
            </p>
            <div className="panel-card">
              <strong>Presets</strong>
              <div className="slash-bar" style={{ marginTop: 8 }}>
                {["legal_core", "kimi_focus", "private", "frontier"].map((p) => (
                  <button
                    key={p}
                    type="button"
                    className="slash-chip"
                    onClick={() => onRunArenaPreset?.(p)}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            {ranking.length > 0 && (
              <div className="quality-card">
                <strong>Ranking</strong>
                {ranking.map((r) => (
                  <div key={String(r.provider)}>
                    <span>
                      {String(r.provider)}
                      {r.source ? ` · ${String(r.source)}` : ""}
                    </span>
                    <b>{String(r.overall ?? "")}</b>
                  </div>
                ))}
              </div>
            )}
            {runs.map((run) => (
              <div className="panel-card" key={`${run.provider}-${run.model}-${run.source}`}>
                <div className="panel-card-heading">
                  <span className="verified-dot" />
                  {String(run.provider)} / {String(run.model)}
                  {run.source ? ` · ${String(run.source)}` : ""}
                </div>
                <p className="clamp">{String(run.content || "").slice(0, 420)}</p>
                <pre className="json-block">{JSON.stringify(run.scores || {}, null, 2)}</pre>
              </div>
            ))}
            {runs.length === 0 && (
              <div className="panel-card">
                <p>
                  Click <strong>Arena</strong> in the slash bar or a preset above to compare
                  Puter, Kimi, safe_local, and more.
                </p>
              </div>
            )}
          </>
        )}

        {activePanel === "openclaw" && (
          <>
            <h2>OpenClaw</h2>
            <p className="muted">
              Agent harness inspired by{" "}
              <a href="https://openclaw.ai/" target="_blank" rel="noreferrer">
                openclaw.ai
              </a>
              : multi-step plans, tool plugins, memory, HITL gates. No autonomous filing.
            </p>
            <div className="panel-card">
              <button type="button" className="slash-chip accent" onClick={() => onRunOpenClaw?.()}>
                Run OpenClaw on current input
              </button>
              <p className="muted tiny" style={{ marginTop: 8 }}>
                Or type <code>/claw your goal…</code> in chat.
              </p>
            </div>
            {(openClawResult || workPayload?.view === "openclaw") && (
              <>
                <div className="quality-card">
                  <strong>Status</strong>
                  <div>
                    {String(
                      openClawResult?.status || workPayload?.status || "—",
                    )}{" "}
                    · run {String(openClawResult?.run_id || workPayload?.run_id || "")}
                  </div>
                </div>
                {clawPlan.length > 0 && (
                  <div className="panel-card">
                    <strong>Plan</strong>
                    <ol>
                      {clawPlan.map((p, i) => (
                        <li key={i}>
                          {String(p.title || p.tool_id)}{" "}
                          <span className="muted">({String(p.tool_id)})</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
                {clawSteps.map((s, i) => (
                  <div className="panel-card" key={i}>
                    <div className="panel-card-heading">
                      <span className="verified-dot" />
                      {String(s.title || s.tool_id)} · {String(s.status)}
                    </div>
                    <p className="clamp">{String(s.output || "").slice(0, 360)}</p>
                  </div>
                ))}
              </>
            )}
            {!openClawResult && workPayload?.view !== "openclaw" && (
              <div className="panel-card">
                <p>No OpenClaw run yet. Plans tools, loads skills, JR clock, citations, memory.</p>
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
