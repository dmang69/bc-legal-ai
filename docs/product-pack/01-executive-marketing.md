# BC Legal AI Platform — Executive Marketing (one-pager)

**Product name:** BC Legal AI Associate / BC Legal AI Platform  
**Positioning:** Supervised enterprise AI workbench for BC legal workflows — **not a lawyer, not legal advice**.  
**Honesty:** Court-ready export remains fail-closed until human gates pass. Public demos are synthetic-only.

---

## Landing-page hero

### Headline
**AI that organizes legal work — humans keep judgment.**

### Subheadlines
1. **One supervised workspace** for chat, agents, research, and drafting — with legal safety locks built in.  
2. **Private when it must be** — local Ollama, gated cloud models, browser user-pays Puter, org quotas and audit.  
3. **BC-ready tooling** — JR clocks, citation gates, Form 66 awareness, BC Laws verification paths.

### Call to action (24 words)
**Start a supervised pilot:** register an org, open the workbench, and keep every draft non-court-ready until your team approves.

---

## Feature sheet (5 bullets)

| Capability | What users get |
|------------|----------------|
| **Conversational intelligence** | Multi-turn chat, specialists, modes, skill-grounded JR/RTB support |
| **Agentic workflows (OpenClaw)** | Multi-step plans, tool plugins, memory, human approval on high-risk steps — no autonomous filing |
| **Multi-model AI base** | Puter (500+ models, user-pays), Kimi long-context, Ollama local, optional OpenAI/Anthropic behind gates |
| **Arena evaluation** | Side-by-side model comparison with legal-aware heuristic scores and presets |
| **Enterprise governance** | Org auth, matter ACL, ethical walls, hash-chained audit, quotas, telemetry, fail-closed court readiness |

---

## Who benefits

| Audience | Value |
|----------|--------|
| **Legal professionals** | Faster triage, research plans, draft scaffolds — supervised, disclaimer-first |
| **Firms / legal ops** | Org admin, provider allowlists, daily quotas, usage telemetry |
| **Developers** | REST APIs, Docker/GHCR, extensible providers and OpenClaw tools |
| **Researchers** | Arena AI comparison, long-context Kimi path, transparent scoring notes |
| **Public sector / clinics** | Local/private paths, synthetic public demo, no false “court-ready AI” claims |

---

## Scenario 1 — Legal research (JR / RTB)

A junior associate pastes a tribunal decision summary and asks for a **research plan** and **JR clock** check. The platform loads BC skill packs, runs allowlisted research links, computes a provisional ATA s.57 timeline with alternatives when finality is uncertain, and returns a structured outline. Every response carries **not legal advice** and **court_ready: false**. Counsel verifies statutes on **BC Laws** before any filing.

---

## Scenario 2 — Contract / document review posture

A legal ops analyst uploads **synthetic** clause text in a private deployment and runs **summarize**, **privilege scan** cues, and **OpenClaw** planning for missing-fact collection. No autonomous send or e-file. High-risk steps require human approval. Outputs remain working drafts for supervising counsel.

---

## Trust & constraints (always on-page)

- Accuracy: deterministic clocks and citation gates where possible; models do not invent statute text as authority.  
- Transparency: provider/model shown; Arena scores are local heuristics, not LMSYS Elo.  
- Privacy: public Space = synthetic only; private inference via Ollama / gated external LLM.  
- Extensibility: providers, skills, OpenClaw tools, REST suite.  
- Security: org isolation, matter ACL, CSRF/session patterns, audit ledger, external LLM opt-in.

---

## Links

| Surface | URL |
|---------|-----|
| GitHub | https://github.com/dmang69/bc-legal-ai |
| Public demo | https://huggingface.co/spaces/Dmang69/bc-legal-ai |
| Container | `ghcr.io/dmang69/bc-legal-ai` |
| BC Laws | https://www.bclaws.gov.bc.ca/ |
