# BC Legal AI Platform — 6-Month Enterprise Pilot Plan

**Program goal:** Supervised pilot of BC Legal AI for synthetic + carefully scoped firm use cases.  
**Hard constraints:** Not legal advice · no autonomous filing · privacy review before external LLMs · public demos synthetic-only.

---

## Success metrics (dashboard)

| Metric | Target (pilot) | Source |
|--------|----------------|--------|
| API uptime | ≥ 99.5% pilot window | Health / load balancer |
| Chat p95 latency | &lt; 8s server path; Puter network-dependent | APM / logs |
| Safety events blocked | Track count; 0 “court_ready true” leaks | Safety tags / audit |
| Hallucination rate (sampled) | Human review sample ≤ 10% critical invents | Weekly review board |
| Citation gate rejects (correct) | Spot-check false acceptance rate | Citation module |
| User satisfaction (CSAT) | ≥ 4.0 / 5 among pilot users | Survey |
| Compliance events | 0 unauthorized external LLM egress | Config + network logs |
| OpenClaw HITL compliance | 100% high-risk tools not auto-approved in pilot | OpenClaw runs |

---

## Phase 0 — Discovery & compliance (Weeks 1–3)

| | |
|--|--|
| **Objectives** | Scope pilot matters (synthetic first); complete privacy/legal review; define success metrics |
| **Duration** | 3 weeks |
| **Roles** | Product, Legal/compliance, Security, Eng lead, Pilot sponsor |

### Deliverables
- [ ] Pilot charter (in/out of scope, data classes allowed)  
- [ ] Data flow diagram (Puter browser vs server LLM vs Ollama)  
- [ ] Risk register (privilege, residency, model vendors)  
- [ ] Success metric baseline dashboard  
- [ ] Decision: enable `ALA_ALLOW_EXTERNAL_LLM`? (default **no**)  

### Risks & mitigations
| Risk | Mitigation |
|------|------------|
| Scope creep to “full firm AI” | Synthetic-only Phase 1–2; written data policy |
| Confusion with public HF Space | Separate URLs; training that demo ≠ production |

### Acceptance
- [ ] Legal sign-off on pilot data classes  
- [ ] Security sign-off on deployment topology  
- [ ] Metrics dashboard mock accepted by sponsor  

---

## Phase 1 — Core platform foundation (Weeks 3–7)

| | |
|--|--|
| **Objectives** | Auth, tenancy, audit, conversational engine, safety gates stable in customer env |
| **Duration** | 4 weeks (overlaps late Phase 0) |
| **Roles** | Backend, Frontend, Security, DevOps |

### Deliverables
- [ ] Deploy API (Docker/Compose or k8s) + Postgres  
- [ ] Org register/login, CSRF/session posture verified  
- [ ] Conversations multi-turn; matter ACL smoke tests  
- [ ] `safe_local` + safety disclaimers validated  
- [ ] Audit ledger write path verified  
- [ ] Runbook: backup, restore, rotate secrets  

### Risks & mitigations
| Risk | Mitigation |
|------|------------|
| SQLite multi-worker issues | Require Postgres for pilot multi-instance |
| Weak passwords / demo creds | Enforce password policy; no shared demo passwords in prod |

### Acceptance
- [ ] `pytest` green in CI against pilot branch  
- [ ] Smoke: register → chat → audit row exists  
- [ ] No confidential data in logs  

---

## Phase 2 — Documents, retrieval, productivity (Weeks 7–12)

| | |
|--|--|
| **Objectives** | Productivity suite + bounded research + JR/citation legal tools in daily workflow |
| **Duration** | 5 weeks |
| **Roles** | Backend, Frontend, Legal SME, Product |

### Deliverables
- [ ] Slash tools: summarize, email, research plan, code  
- [ ] Web research allowlist + org flag training  
- [ ] JR clock HITL labeling in UI  
- [ ] Citation fail-closed behaviour documented  
- [ ] Skills packs for RTB/JR loaded and reviewed by counsel  
- [ ] Work panel UX for tools/sources  

### Risks & mitigations
| Risk | Mitigation |
|------|------------|
| Users treat JR clock as filing deadline | UI “candidate / HITL required” copy; training |
| Web research over-fetch | Default off; host allowlist |

### Acceptance
- [ ] 10 synthetic research tasks completed by pilot users  
- [ ] Zero statute text presented as “verified” without BC Laws link  
- [ ] Legal SME sign-off on disclaimer language  

---

## Phase 3 — Local models, long-context, Arena (Weeks 11–16)

| | |
|--|--|
| **Objectives** | Private Ollama path; Puter/Kimi browser base; Arena evaluation for model selection |
| **Duration** | 5 weeks (overlap) |
| **Roles** | ML/platform eng, Frontend, Security, FinOps |

### Deliverables
- [ ] Ollama on pilot hardware; `private_local` mode tested  
- [ ] Puter as default AI base (user-pays documented)  
- [ ] Kimi long-context path for large synthetic records  
- [ ] Arena presets (`legal_core`, `kimi_focus`, `private`) used in eval workshops  
- [ ] Org allowlists: puter, kimi, safe_local, ollama  
- [ ] Cost note: Puter billing is user-side; server keys remain gated  

### Risks & mitigations
| Risk | Mitigation |
|------|------------|
| Confidential data to Puter/browser vendors | Policy: synthetic or approved data classes only; prefer Ollama for sensitive |
| Arena scores over-trusted | Label “heuristic not Elo”; human winner |

### Acceptance
- [ ] Side-by-side Arena workshop with 5 prompts scored by humans  
- [ ] Sensitive matter path uses Ollama/safe_local only  
- [ ] No `ALA_ALLOW_EXTERNAL_LLM=1` without DPIA  

---

## Phase 4 — Agentic workflows & hardening (Weeks 15–20)

| | |
|--|--|
| **Objectives** | OpenClaw multi-step workflows in pilot; enterprise hardening |
| **Duration** | 5 weeks |
| **Roles** | Backend, Security, Legal, Product, SRE |

### Deliverables
- [ ] OpenClaw `/claw` training for pilot users  
- [ ] HITL policy: which tools may `auto_approve` (default none high-risk)  
- [ ] Rate limits, backup drills, incident runbook  
- [ ] Pen-test or structured security review of auth/ACL  
- [ ] Plugin/tool extension guide for internal developers  
- [ ] Export/court-ready gates reaffirmed fail-closed  

### Risks & mitigations
| Risk | Mitigation |
|------|------------|
| Users expect autonomous filing | Product copy + blocked actions list |
| Agent over-permission | Tool risk levels + approval gates |

### Acceptance
- [ ] 20 OpenClaw runs reviewed; 100% high-risk steps HITL-compliant  
- [ ] Security findings triaged (P0 closed)  
- [ ] Rollback procedure tested (image pin)  

---

## Phase 5 — Pilot launch & production readiness (Weeks 20–26)

| | |
|--|--|
| **Objectives** | Controlled pilot go-live; training; feedback; production readiness decision |
| **Duration** | 6 weeks |
| **Roles** | All + Pilot users + Sponsor |

### Deliverables
- [ ] Pilot launch checklist complete  
- [ ] User training (2 sessions + written guide)  
- [ ] Feedback loop (weekly office hours + issue tracker)  
- [ ] Dashboard live (uptime, latency, safety, CSAT)  
- [ ] Production readiness report (go / no-go / conditional)  
- [ ] Roadmap for SSO, vector RAG, GraphQL if approved  

### Risks & mitigations
| Risk | Mitigation |
|------|------------|
| Support load | Office hours; synthetic-first onboarding |
| Feature requests break safety | Change control; safety locks non-negotiable |

### Acceptance
- [ ] CSAT ≥ 4.0 or documented remediation plan  
- [ ] Zero critical compliance incidents  
- [ ] Written go/no-go from Legal + Security + Sponsor  

---

## Roles matrix (RACI summary)

| Workstream | Product | Eng | Security | Legal | Data/Ops |
|------------|---------|-----|----------|-------|----------|
| Charter & metrics | A | C | C | A | C |
| Platform deploy | C | R/A | C | I | R |
| AI providers policy | C | R | A | A | C |
| Skills / legal content | C | C | I | A | I |
| OpenClaw HITL policy | A | R | C | A | I |
| Pilot training | A | C | I | C | I |
| Prod readiness | A | R | A | A | R |

R = Responsible, A = Accountable, C = Consulted, I = Informed  

---

## Pilot customer rollout checklist

### Before access
- [ ] NDA / pilot agreement  
- [ ] Data class policy acknowledged (synthetic vs client)  
- [ ] Accounts provisioned (owner + 2–5 users)  
- [ ] MFA / SSO plan if required by org  

### Environment
- [ ] API URL + UI URL documented  
- [ ] Backups enabled  
- [ ] `ALA_ALLOW_EXTERNAL_LLM=0` unless approved  
- [ ] Ollama optional path tested  

### Training
- [ ] Disclaimers & court_ready explained  
- [ ] OpenClaw demo (HITL)  
- [ ] Arena workshop (heuristics)  
- [ ] BC Laws verification habit  

### During pilot
- [ ] Weekly metrics review  
- [ ] Incident contact card  
- [ ] Feedback form link  

### Exit / scale
- [ ] Export of synthetic learnings  
- [ ] Delete or retain decision per policy  
- [ ] Scale proposal or wind-down  

---

## Timeline (Gantt-style)

```
Month 1:  [==== Phase 0 ====][== Phase 1 ==]
Month 2:  [======== Phase 1/2 ========]
Month 3:  [==== Phase 2 ====][== Phase 3 ==]
Month 4:  [======== Phase 3/4 ========]
Month 5:  [==== Phase 4 ====][== Phase 5 ==]
Month 6:  [======== Phase 5 ========] → Go/No-Go
```

---

## Dependency notes

| Need environment detail before coding | Examples |
|---------------------------------------|----------|
| Cloud vs on-prem | Azure/AWS/k8s bare metal |
| GPU availability | Ollama model size |
| IdP | Entra ID / Okta OIDC |
| Data residency | Canadian region only? |
| Budget for external LLM | Puter user-pays vs org keys |

Do **not** generate cloud-specific manifests until those are confirmed.
