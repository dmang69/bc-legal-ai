import { useCallback, useEffect, useMemo, useState } from "react";
import { Composer } from "./components/Composer";
import { MessageList } from "./components/MessageList";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { WorkPanel } from "./components/WorkPanel";
import {
  aiSuite,
  arenaCompare,
  chatCapabilities,
  checkQuota,
  createConversation,
  createMatter,
  getOrgAiSettings,
  getOrgTelemetry,
  getToken,
  healthCheck,
  listConversations,
  listMatters,
  listModelProviders,
  listModes,
  listSpecialists,
  login,
  logout,
  listFeatures,
  openClawRun,
  register,
  sendMessage,
  setToken,
  type FeaturesManifest,
  type Matter as ApiMatter,
  type OrgAiSettings,
  type ProviderMeta,
  type Session,
  updateOrgAiSettings,
  webResearch,
} from "./lib/api";
import {
  DEFAULT_KIMI_MODEL,
  DEFAULT_PUTER_MODEL,
  LEGAL_PUTER_SYSTEM,
  arenaClientRuns,
  puterChat,
} from "./lib/puterClient";
import { findSensitiveText } from "./lib/security";
import type {
  AppMode,
  AttachmentItem,
  ChatMessage,
  ProviderOption,
  ReasoningMode,
  ThreadItem,
  WorkPanel as WorkPanelType,
} from "./types";
import "./styles.css";

const SLASH_TOOLS = [
  { id: "/summarize", label: "Summarize", hint: "/summarize: text…" },
  { id: "/email", label: "Email", hint: "/email purpose…" },
  { id: "/creative", label: "Creative", hint: "/creative prompt…" },
  { id: "/research", label: "Research", hint: "/research query…" },
  { id: "/code", label: "Code", hint: "/code snippet…" },
  { id: "/debug", label: "Debug", hint: "/debug error + code…" },
  { id: "/claw", label: "OpenClaw", hint: "/claw goal for multi-step agent…" },
  { id: "/kimi", label: "Kimi", hint: "/kimi deep long-context question…" },
  { id: "/hearing", label: "Hearing prep", hint: "/hearing prep RTB JR record + binder…" },
];

function nowTime(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function App() {
  const [appMode] = useState<AppMode>(
    import.meta.env.VITE_APP_MODE === "public_demo" ? "public_demo" : "private",
  );
  const [session, setSession] = useState<Session | null>(null);
  const [authEmail, setAuthEmail] = useState("demo@synthetic.invalid");
  const [authPassword, setAuthPassword] = useState("securepass99");
  const [authOrg, setAuthOrg] = useState("Demo Firm");
  const [authError, setAuthError] = useState<string | null>(null);
  const [authBusy, setAuthBusy] = useState(false);

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [threads, setThreads] = useState<ThreadItem[]>([]);
  const [activeThreadId, setActiveThreadId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [warning, setWarning] = useState<string | null>(null);

  const [matters, setMatters] = useState<ApiMatter[]>([]);
  const [matterId, setMatterId] = useState("");
  const [reasoningMode, setReasoningMode] = useState<ReasoningMode>("balanced");
  const [modes, setModes] = useState<Array<{ id: string; label: string }>>([]);
  const [specialists, setSpecialists] = useState<Array<{ id: string; name: string }>>([]);
  const [selectedAgentId, setSelectedAgentId] = useState("bc_legal_associate");
  const [providers, setProviders] = useState<ProviderOption[]>([]);
  const [providerId, setProviderId] = useState("puter");
  const [modelId, setModelId] = useState(DEFAULT_PUTER_MODEL);
  const [activePanel, setActivePanel] = useState<WorkPanelType>("tools");
  const [health, setHealth] = useState<string>("checking…");
  const [suiteNote, setSuiteNote] = useState("");
  const [workPayload, setWorkPayload] = useState<Record<string, unknown> | null>(null);
  const [arenaResult, setArenaResult] = useState<Record<string, unknown> | null>(null);
  const [openClawResult, setOpenClawResult] = useState<Record<string, unknown> | null>(null);
  const [featuresManifest, setFeaturesManifest] = useState<FeaturesManifest | null>(null);
  const [orgSettings, setOrgSettings] = useState<OrgAiSettings | null>(null);
  const [telemetry, setTelemetry] = useState<Record<string, unknown> | null>(null);
  const [quotaLine, setQuotaLine] = useState("");

  const matter = useMemo(() => {
    const m = matters.find((x) => x.matter_id === matterId);
    return m
      ? {
          id: m.matter_id,
          name: m.title,
          synthetic: m.synthetic,
          privilege: "Matter ACL enforced",
          matter_id: m.matter_id,
        }
      : { id: "", name: "No matter selected", synthetic: true, privilege: "General chat" };
  }, [matters, matterId]);

  const agents = useMemo(
    () =>
      specialists.map((s) => ({
        id: s.id,
        name: s.name,
        description: s.id,
      })),
    [specialists],
  );

  const bootstrap = useCallback(async () => {
    const h = await healthCheck();
    setHealth(
      h.ok
        ? `API ok · ${h.phase || "m1"} · db ${h.db_backend || "?"} · ${h.session_auth || "auth"}`
        : "API offline — start uvicorn backend.api.main:app",
    );
    if (!getToken()) return;
    try {
      const [prov, caps, suite, mats, convs, modeList, specs, settings, tel, q, feats] =
        await Promise.all([
          listModelProviders(),
          chatCapabilities().catch(() => ({})),
          aiSuite().catch(() => ({})),
          listMatters().catch(() => ({ matters: [] as ApiMatter[] })),
          listConversations().catch(() => ({ conversations: [] })),
          listModes().catch(() => ({ modes: [] })),
          listSpecialists().catch(() => ({ specialists: [] })),
          getOrgAiSettings().catch(() => null),
          getOrgTelemetry().catch(() => null),
          checkQuota(providerId).catch(() => null),
          listFeatures().catch(() => null),
        ]);
      if (feats && "features" in feats) {
        setFeaturesManifest(feats as FeaturesManifest);
      }
      const mappedProviders: ProviderOption[] = (prov.providers || []).map(
        (p: ProviderMeta) => ({
          id: p.id,
          name: p.name,
          configured: p.configured,
          local: p.local,
          client_side: p.client_side,
          user_pays: p.user_pays,
          models: p.models,
          default_model: p.default_model,
        }),
      );
      setProviders(mappedProviders);
      const nextProvider =
        settings?.default_provider ||
        mappedProviders.find((p) => p.id === "puter")?.id ||
        mappedProviders[0]?.id ||
        "puter";
      setProviderId(nextProvider);
      const selected = mappedProviders.find((p) => p.id === nextProvider);
      if (selected?.default_model) setModelId(selected.default_model);
      else if (selected?.models?.[0]) setModelId(selected.models[0]);
      setMatters(mats.matters || []);
      if ((mats.matters || [])[0]) setMatterId(mats.matters[0]!.matter_id);
      setModes((modeList.modes || []).map((m) => ({ id: m.id, label: m.label })));
      setSpecialists(specs.specialists || []);
      setOrgSettings(settings);
      setTelemetry(tel as Record<string, unknown> | null);
      if (q) {
        setQuotaLine(
          q.allowed
            ? `Quota OK · ${q.usage_today?.remaining ?? "?"} remaining today`
            : `Quota blocked: ${q.reason}`,
        );
      }
      const insp = (suite as { inspirations?: string[] }).inspirations;
      setSuiteNote(
        insp?.length
          ? `Suite: ${insp.slice(0, 4).join(" · ")}…`
          : String((caps as { product?: string }).product || "BC Legal AI"),
      );
      const mapped: ThreadItem[] = (convs.conversations || []).map((c) => ({
        id: c.conversation_id,
        title: c.title || "Chat",
        matterId: c.matter_id,
        updatedAt: c.updated_at || "",
      }));
      setThreads(mapped);
      if (mapped[0]) setActiveThreadId(mapped[0].id);
    } catch (e) {
      setWarning(String(e));
    }
  }, [providerId]);

  useEffect(() => {
    if (getToken()) {
      setSession({
        token: getToken()!,
        user: {
          user_id: "",
          org_id: "",
          email: "session",
          display_name: "Signed in",
          role: "owner",
        },
      });
    }
    void bootstrap();
  }, [bootstrap]);

  async function handleLogin(isRegister: boolean) {
    setAuthBusy(true);
    setAuthError(null);
    try {
      const s = isRegister
        ? await register({
            org_name: authOrg,
            email: authEmail,
            password: authPassword,
            display_name: authEmail.split("@")[0],
          })
        : await login(authEmail, authPassword);
      setSession(s);
      await bootstrap();
    } catch (e) {
      setAuthError(String(e));
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleLogout() {
    await logout();
    setSession(null);
    setThreads([]);
    setMessages([]);
    setToken(null);
  }

  async function createNewChat() {
    if (!getToken()) {
      setWarning("Sign in to create a live conversation.");
      return;
    }
    try {
      const c = await createConversation({
        title: "New conversation",
        chat_type: matterId ? "matter" : "general",
        matter_id: matterId || undefined,
        model_mode: reasoningMode,
        specialist: selectedAgentId,
      });
      const item: ThreadItem = {
        id: c.conversation_id,
        title: c.title,
        matterId: c.matter_id,
        updatedAt: "Now",
      };
      setThreads((t) => [item, ...t]);
      setActiveThreadId(c.conversation_id);
      setMessages([
        {
          id: crypto.randomUUID(),
          role: "system",
          content:
            "Live conversation. Not legal advice. Slash tools: /summarize /email /research /code · providers in toolbar · Arena & Admin in work panel.",
          createdAt: nowTime(),
          status: "complete",
        },
      ]);
      setInput("");
    } catch (e) {
      setWarning(String(e));
    }
  }

  async function ensureConversation(): Promise<string> {
    if (activeThreadId) return activeThreadId;
    const c = await createConversation({
      title: "New conversation",
      chat_type: "general",
      model_mode: reasoningMode,
      specialist: selectedAgentId,
    });
    setActiveThreadId(c.conversation_id);
    setThreads((t) => [
      { id: c.conversation_id, title: c.title, updatedAt: "Now" },
      ...t,
    ]);
    return c.conversation_id;
  }

  function handleFilesSelected(files: FileList) {
    const next: AttachmentItem[] = Array.from(files).map((file) => ({
      id: crypto.randomUUID(),
      name: file.name,
      size: file.size,
      type: file.type,
      state: appMode === "public_demo" ? "blocked" : "queued",
      reason: appMode === "public_demo" ? "Uploads disabled in public demo" : undefined,
    }));
    setAttachments((c) => [...c, ...next]);
  }

  async function sendChat() {
    const trimmed = input.trim();
    if (!trimmed || busy) return;
    if (appMode === "public_demo") {
      const sens = findSensitiveText(trimmed);
      if (sens.length) {
        setWarning(`Blocked: ${sens.join(", ")}`);
        return;
      }
    }
    if (!getToken()) {
      setWarning("Sign in to use the live chat API.");
      return;
    }
    setWarning(null);
    setBusy(true);
    const pendingId = crypto.randomUUID();
    setMessages((m) => [
      ...m,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
        createdAt: nowTime(),
        status: "complete",
      },
      {
        id: pendingId,
        role: "assistant",
        content: "Thinking…",
        createdAt: nowTime(),
        status: "streaming",
      },
    ]);
    setInput("");
    try {
      const cid = await ensureConversation();
      let clientContent: string | undefined;
      let usedModel = modelId || "";

      // Puter / Kimi: browser puter.ai.chat() then persist via API with safety gates.
      if (providerId === "puter" || providerId === "kimi") {
        const historyMsgs = messages
          .filter((m) => m.role === "user" || m.role === "assistant")
          .slice(-16)
          .map((m) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
          }));
        const browserModel =
          modelId ||
          (providerId === "kimi" ? DEFAULT_KIMI_MODEL : DEFAULT_PUTER_MODEL);
        const puterResult = await puterChat({
          messages: [
            { role: "system", content: LEGAL_PUTER_SYSTEM },
            ...historyMsgs,
            { role: "user", content: trimmed },
          ],
          model: browserModel,
        });
        clientContent = puterResult.content;
        usedModel = puterResult.model;
      }

      const res = await sendMessage(cid, {
        content: trimmed,
        provider: providerId,
        model: usedModel,
        client_content: clientContent,
      });
      const meta = res.assistant.meta || {};
      setMessages((m) =>
        m.map((msg) =>
          msg.id === pendingId
            ? {
                ...msg,
                content: res.assistant.content,
                status: "complete",
                citations: meta.citations,
                actions: meta.actions,
                warnings: meta.warnings,
                provider: meta.provider || String(meta.controls?.provider || providerId),
                model: meta.model || usedModel,
                toolActivity: meta.tool_activity,
                workPanel: meta.work_panel as Record<string, unknown> | undefined,
              }
            : msg,
        ),
      );
      if (meta.work_panel) {
        setWorkPayload(meta.work_panel as Record<string, unknown>);
        setActivePanel("tools");
      }
      setThreads((t) =>
        t.map((th) =>
          th.id === cid
            ? {
                ...th,
                title:
                  th.title === "New conversation" || th.title === "New chat"
                    ? trimmed.slice(0, 48)
                    : th.title,
                updatedAt: "Now",
              }
            : th,
        ),
      );
      const q = await checkQuota(providerId).catch(() => null);
      if (q) {
        setQuotaLine(
          q.allowed
            ? `Quota OK · ${q.usage_today?.remaining ?? "?"} remaining`
            : `Quota: ${q.reason}`,
        );
      }
    } catch (e) {
      setMessages((m) =>
        m.map((msg) =>
          msg.id === pendingId
            ? {
                ...msg,
                content: `Error: ${String(e)}`,
                status: "warning",
              }
            : msg,
        ),
      );
    } finally {
      setBusy(false);
      setAttachments([]);
    }
  }

  async function runArena(preset?: string) {
    const prompt =
      input.trim() ||
      messages.filter((m) => m.role === "user").slice(-1)[0]?.content ||
      "Explain JR Form 66 briefly. Not legal advice.";
    setBusy(true);
    try {
      const providersToRun = preset
        ? []
        : [providerId, "kimi", "safe_local"].filter((v, i, a) => a.indexOf(v) === i);
      // Browser completions for puter/kimi (Arena AI client merge)
      const clientTargets = preset
        ? ["puter", "kimi"]
        : providersToRun.filter((p) => p === "puter" || p === "kimi");
      const client_runs = await arenaClientRuns(prompt, clientTargets, {
        puter: modelId || DEFAULT_PUTER_MODEL,
        kimi: DEFAULT_KIMI_MODEL,
      }).catch(() => []);
      const result = await arenaCompare(prompt, providersToRun, {
        preset: preset || (providersToRun.length ? "" : "legal_core"),
        client_runs,
        models: {
          puter: modelId || DEFAULT_PUTER_MODEL,
          kimi: DEFAULT_KIMI_MODEL,
        },
      });
      setArenaResult(result as unknown as Record<string, unknown>);
      setActivePanel("arena");
      setWorkPayload({ view: "arena", title: "Arena AI comparison", preset: preset || "custom" });
    } catch (e) {
      setWarning(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function runOpenClaw() {
    const goal =
      input.trim() ||
      messages.filter((m) => m.role === "user").slice(-1)[0]?.content ||
      "Triage a BC RTB judicial review workflow and list next steps.";
    setBusy(true);
    try {
      const result = await openClawRun({ goal, auto_approve: false, execute: true });
      setOpenClawResult(result as unknown as Record<string, unknown>);
      setActivePanel("openclaw");
      setWorkPayload({
        view: "openclaw",
        title: "OpenClaw agent",
        run_id: result.run_id,
        status: result.status,
        plan: result.plan,
        steps: result.steps,
      });
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.summary,
          createdAt: nowTime(),
          status: "complete",
          provider: "openclaw",
          model: "legal-harness",
          warnings: result.warnings,
          workPanel: {
            view: "openclaw",
            run_id: result.run_id,
            plan: result.plan,
            steps: result.steps,
          },
        },
      ]);
    } catch (e) {
      setWarning(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function runWebResearch() {
    const q = input.trim() || "Residential Tenancy Act BC";
    setBusy(true);
    try {
      const r = await webResearch(q);
      setWorkPayload({ view: "research", title: "Web research", ...r });
      setActivePanel("sources");
    } catch (e) {
      setWarning(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function saveOrgSettings(patch: Partial<OrgAiSettings>) {
    try {
      const s = await updateOrgAiSettings(patch);
      setOrgSettings(s);
      setWarning(null);
      const tel = await getOrgTelemetry().catch(() => null);
      if (tel) setTelemetry(tel as Record<string, unknown>);
    } catch (e) {
      setWarning(String(e));
    }
  }

  async function addSyntheticMatter() {
    try {
      const m = await createMatter(`Synthetic matter ${new Date().toLocaleDateString()}`);
      setMatters((x) => [m, ...x]);
      setMatterId(m.matter_id);
    } catch (e) {
      setWarning(String(e));
    }
  }

  if (!session && !getToken()) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <div className="brand-mark">BC</div>
          <h1>BC Legal AI Associate</h1>
          <p className="muted">
            Conversational workspace with Puter AI base (500+ models, user-pays) and
            multi-provider suite. Not legal advice.
          </p>
          <label>
            Organization
            <input value={authOrg} onChange={(e) => setAuthOrg(e.target.value)} />
          </label>
          <label>
            Email
            <input value={authEmail} onChange={(e) => setAuthEmail(e.target.value)} />
          </label>
          <label>
            Password (10+ chars)
            <input
              type="password"
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
            />
          </label>
          {authError && <div className="composer-warning">{authError}</div>}
          <div className="auth-actions">
            <button disabled={authBusy} onClick={() => void handleLogin(false)}>
              Sign in
            </button>
            <button disabled={authBusy} className="secondary" onClick={() => void handleLogin(true)}>
              Register org
            </button>
          </div>
          <p className="muted tiny">{health}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
        onNewChat={() => void createNewChat()}
        onSelectThread={setActiveThreadId}
        userLabel={session?.user.email || "Signed in"}
        onLogout={() => void handleLogout()}
      />
      <main className="main-shell">
        <TopBar
          appMode={appMode}
          matter={matter}
          matters={matters.map((m) => ({
            id: m.matter_id,
            name: m.title,
            synthetic: m.synthetic,
          }))}
          reasoningMode={reasoningMode}
          modes={modes.length ? modes : [
            { id: "balanced", label: "Balanced" },
            { id: "deep", label: "Deep" },
            { id: "private_local", label: "Private Local" },
          ]}
          providers={providers}
          providerId={providerId}
          modelId={modelId}
          health={health}
          quotaLine={quotaLine}
          onMatterChange={setMatterId}
          onModeChange={(m) => setReasoningMode(m as ReasoningMode)}
          onProviderChange={(id) => {
            setProviderId(id);
            const p = providers.find((x) => x.id === id);
            if (p?.default_model) setModelId(p.default_model);
            else if (p?.models?.[0]) setModelId(p.models[0]);
          }}
          onModelChange={setModelId}
          onNewMatter={() => void addSyntheticMatter()}
        />
        <div className="workspace-grid">
          <section className="conversation-column">
            <div className="conversation-banner">
              <div>
                <span className="eyebrow">Puter · OpenClaw · Kimi · Arena AI</span>
                <h1>Conversational Legal Workspace</h1>
                <p>
                  {suiteNote ||
                    "Puter AI base · OpenClaw agents · Kimi long-context · Arena AI comparison · legal safety gates."}
                </p>
              </div>
              <div className="trust-stack">
                <span>◈ {matter.privilege}</span>
                <span>◈ court_ready: false</span>
                <span>
                  ◈ {providerId}
                  {modelId ? `/${modelId}` : ""}
                </span>
              </div>
            </div>
            <div className="slash-bar" aria-label="Slash tools">
              {SLASH_TOOLS.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  className="slash-chip"
                  title={t.hint}
                  onClick={() => setInput((v) => (v ? v : `${t.id} `))}
                >
                  {t.label}
                </button>
              ))}
              <button type="button" className="slash-chip accent" onClick={() => void runArena()}>
                Arena AI
              </button>
              <button type="button" className="slash-chip" onClick={() => void runOpenClaw()}>
                OpenClaw
              </button>
              <button type="button" className="slash-chip" onClick={() => void runWebResearch()}>
                Research
              </button>
              <button
                type="button"
                className="slash-chip"
                onClick={() => setActivePanel("admin")}
              >
                Org Admin
              </button>
            </div>
            <MessageList messages={messages} />
            <Composer
              value={input}
              appMode={appMode}
              busy={busy}
              attachments={attachments}
              agents={agents.length ? agents : [{ id: "bc_legal_associate", name: "BC Legal Associate" }]}
              selectedAgentId={selectedAgentId}
              warning={warning}
              onChange={setInput}
              onAgentChange={setSelectedAgentId}
              onFilesSelected={handleFilesSelected}
              onRemoveAttachment={(id) =>
                setAttachments((c) => c.filter((a) => a.id !== id))
              }
              onSend={() => void sendChat()}
            />
          </section>
          <WorkPanel
            activePanel={activePanel}
            matter={matter}
            agents={agents}
            selectedAgentId={selectedAgentId}
            onPanelChange={setActivePanel}
            workPayload={workPayload}
            arenaResult={arenaResult}
            openClawResult={openClawResult}
            featuresManifest={featuresManifest}
            orgSettings={orgSettings}
            telemetry={telemetry}
            providers={providers}
            onSaveSettings={(p) => void saveOrgSettings(p)}
            onRefreshTelemetry={() => {
              void getOrgTelemetry()
                .then((t) => setTelemetry(t as unknown as Record<string, unknown>))
                .catch((e) => setWarning(String(e)));
            }}
            onRunOpenClaw={() => void runOpenClaw()}
            onRunArenaPreset={(p) => void runArena(p)}
          />
        </div>
      </main>
    </div>
  );
}
