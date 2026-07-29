# Product Vision Repository Audit — AI Legal Assistant Studio

**Date:** 2026-07-23  
**Repository:** `bc-legal-ai`  
**Vision audited against:** sophisticated, customizable, AI-powered legal assistant studio for drafting, research, document analysis, automation, security, compliance, and collaboration.  
**Current product identity:** BC Legal AI Associate — human-supervised legal research, evidence, drafting, and matter-support platform for British Columbia.

## Executive finding

The repository is directionally aligned with the requested product vision, but its implemented maturity is still **prototype / internal-alpha foundation**, not a completed associate-level legal assistant studio.

The strongest existing assets are:

- BC-specific legal safety posture: not legal advice, human supervision, no autonomous filing/sending/settlement/privilege waiver.
- Matter-oriented architecture with early identity, matters, audit, evidence, consent, privilege, and citation modules.
- A controlling product definition for a conversational legal operating environment.
- A React/Vite workspace scaffold with chat modes, source/status panels, and safety-gate messaging.
- Extensive legal-domain scaffolding for BC tenancy, judicial review, evidence matrices, privilege, citations, deadlines, post-resolution, and court packages.
- An engineering roadmap that correctly prioritizes identity, matter isolation, ingestion, official-source retrieval, human review, and production hardening before public real-client use.

The largest gaps against the broader studio vision are:

- Full long-context document ingestion, OCR, page-level provenance, and persistent retrieval are not production-complete.
- Live AI drafting/editing, side-by-side artifact editing, and court-ready export remain incomplete.
- Personalization controls such as tone, formality, response length, language, legal-domain focus, model selection, and user/org profiles are not yet implemented as first-class product features.
- Collaboration features such as shared workspaces, task assignment, annotations, and version history are only partially anticipated.
- Enterprise security claims such as end-to-end encryption, advanced RBAC/ABAC, MFA, SSO, and GDPR-grade governance are not yet fully implemented.
- The UI is still a scaffold and demo-oriented; many navigation items are marked unavailable.
- There are visible implementation defects that must be fixed before treating the current UI/API as stable.

## Capability-by-capability audit

| Vision capability | Current repo evidence | Maturity | Gap / implication |
|---|---|---:|---|
| Conversational legal workspace similar to ChatGPT/Claude/Kimi | `docs/CONVERSATIONAL_WORKSPACE_SPEC.md`; `apps/platform-ui/src/workspace/ConversationalWorkspace.tsx`; `/v1/platform/workspace/analyze` | Partial | Modes and safety-gate UX exist, but no full LLM orchestration, persistent rich chat UX, streaming agent execution, model selector, or real document-grounded responses yet. |
| Legal document drafting across contracts, briefs, filings, forms | `docs/PRODUCT_DESCRIPTION.md`; `backend/platform/drafting.py`; templates under `templates/` and `knowledgebase/templates/` | Scaffold / partial | Drafting exists as a target and some specific templates exist, but there is no full artifact editor, revision workflow, style controls, clause library, or robust DOCX/PDF court export pipeline. |
| Multi-turn legal strategy discussion | Workspace modes and classifier detect JR/RTB/deadline contexts | Early scaffold | Current `/workspace/analyze` is safe triage, not associate-level reasoning. It explicitly blocks court-ready treatment and requests sources/review. |
| Long-context legal document analysis | Product docs require chunked, page-indexed ingestion; evidence modules exist | Partial design; limited runtime | Text upload/quarantine is partial. OCR, page-level citations, media handling, durable retrieval, and no-context-window truncation guarantees remain unfinished. |
| Research assistant with authoritative citations | BC Laws discipline, citation verifier scaffolds, source registry, fail-closed gates | Partial | Official law retrieval and citation verification are core to the architecture, but live comprehensive case/statute retrieval, treatment analysis, and point-in-time law are not production-complete. |
| Customizable tone/formality/length/languages/domain focus | Product vision asks for this; some accessibility/multilingual notes exist | Mostly absent | Need profile/settings system, prompt policy layer, per-matter/persona settings, multilingual UX, and legal-domain routing. |
| Multi-mode workflow: chat, drafting, research, automation | Workspace mode set: general, matter, document, research, drafting, agent | Scaffold | Modes exist mostly as labels and safety routing. Need real mode-specific tools, panels, persistence, permissions, and task orchestration. |
| Task automation panel | Agent mode warnings and HITL scaffolds | Early scaffold | No mature automations for contract review, compliance tracking, task queues, approvals, or recurring workflows. |
| Security / compliance / privilege | Strong docs and modules: privilege, consent, audit, conflicts, public demo controls | Partial, strong direction | Enterprise-grade security is not complete. MFA, SSO, encryption at rest, per-matter keys, full RBAC/ABAC, privacy impact processes, and hardening are still roadmap items. |
| Collaboration / shared workspaces | Matter model, conversations, audit, task roadmap | Mostly absent / early | Need org workspaces, comments/annotations, assignments, role-based collaboration, document versioning, activity feeds, and notification workflows. |
| Cross-platform studio | React/Vite UI, Tauri scaffold, PWA notes | Scaffold | Delivery shells exist but are not signed, store-ready, or feature-complete. |
| Legal ethics / unauthorized-practice controls | Very strong in README, `PRODUCT_STATUS.md`, roadmap, hard stops | Strong design; partial enforcement | Must keep this as a core differentiator: supervised-support platform, not autonomous legal advice. Enforcement must be deepened at API/tool/export layers. |

## Existing architecture strengths

1. **Correct legal product boundary**
   - The repo repeatedly states the product is not a lawyer and not legal advice.
   - It frames AI as support under human supervision.
   - It blocks court-ready output without evidence, citation, privilege, procedure, and approval gates.

2. **Matter-first architecture**
   - The product is built around matters, ACLs, consent, audit, evidence, citations, and conversations.
   - This aligns better with real legal practice than a generic chat wrapper.

3. **Grounding and verification discipline**
   - The roadmap correctly prioritizes official law, point-in-time legal sources, citation verification, and evidence provenance.
   - It rejects premature fine-tuning and autonomous agents.

4. **Pragmatic technical strategy**
   - Modular monolith first, PostgreSQL + pgvector, S3-compatible object storage, Redis workers.
   - Defers Neo4j, microservices, fine-tuning, and whole-PC indexing until justified.

5. **Safety-first UX direction**
   - The current workspace exposes trust badges for evidence, law, human review, and privacy.
   - This maps well to legal professionals’ need to know what is verified, partial, pending, or blocked.

## Critical product gaps to close

### 1. Studio personalization layer

The vision emphasizes Monica/Copilot-like customizability. The repository needs a first-class settings architecture:

- User and organization preferences.
- Matter-specific drafting defaults.
- Tone, formality, response length, language, jurisdiction, legal-domain focus.
- Output format preferences.
- Model/tool routing preferences subject to consent and privilege.
- Safe defaults that cannot override legal gates.

### 2. True document workspace

The platform needs a side-by-side document environment:

- Draft artifacts beside chat.
- Clause extraction and comparison.
- Revision history and redlines.
- Comments/annotations.
- Export to DOCX, searchable PDF, PDF/A, and bundle ZIP.
- Every factual/legal statement linked to source evidence or authority.

### 3. Production ingestion and retrieval

The current vision depends on Kimi-like long-context document handling. The implementation must become chunked, indexed, and provenance-preserving:

- File upload quarantine.
- OCR and layout extraction.
- Page/paragraph/timestamp indexing.
- Duplicate/version detection.
- Metadata and EXIF extraction.
- Matter-scoped embeddings.
- Retrieval that never silently truncates the record.

### 4. Associate-level research engine

The research layer needs to evolve from fail-closed scaffolding to verified retrieval:

- Official BC Laws ingestion and version tracking.
- Court and tribunal authority ingestion.
- Citation parser and verifier.
- Pinpoint support matching.
- Case treatment / appellate history.
- Jurisdiction and binding-weight analysis.
- Court-ready output block unless authorities pass gates.

### 5. Collaboration and work management

The vision includes legal team productivity. Required additions:

- Shared matter workspaces.
- Assignments, due dates, and task states.
- Team comments and contextual annotations.
- Document version history.
- Approval workflows.
- Notifications and audit trail views.

### 6. Security/compliance hardening

The repository correctly avoids overclaiming, but the target studio needs deeper implementation:

- MFA and possibly SSO/OIDC.
- Full RBAC/ABAC and ethical walls.
- Encryption at rest and in transit.
- Per-matter key strategy.
- Audit ledger immutability and export.
- Retention, legal holds, and destruction workflows.
- Privacy impact assessment and vendor/model review.
- Clear distinction between true E2EE and AI-enabled workspace encryption.

## Implementation defects observed during audit

These are not full code-review findings, but they are immediate stability concerns:

1. `backend/api/platform_routes.py` uses `re.finditer(...)` in `/workspace/analyze`, but the visible imports do not include `import re`.
2. `apps/platform-ui/src/lib/api.ts` defines `verifyCitation(citation_text, expected_topic)` but sends `JSON.stringify({ content })`; `content` is undefined and the route expects citation fields.
3. The workspace UI uses demo matter/data by default and calls unauthenticated analysis for the safety gateway, which is acceptable for synthetic scaffold but not for real matter operation.
4. Several UI navigation items are explicitly unavailable: search chats, projects, calendar, court packages, downloads, settings.
5. Public-demo and local-platform boundaries must remain strict; no real client documents should be processed through public or synthetic modes.

## Recommended product positioning

Use the broadened vision as an aspirational **studio strategy**, but keep public claims anchored to the repository’s current maturity:

- **Now:** supervised BC legal workbench prototype / internal-alpha foundation.
- **Next:** secure matter-scoped conversational workspace with ingestion, research, citation, and drafting gates.
- **Later:** full customizable legal assistant studio for lawyers and authorized legal teams.

Avoid claiming:

- Autonomous legal advice.
- Production-grade E2EE if server-side AI reads content.
- Court-ready drafting before citation/procedure/privilege approval gates.
- GDPR/enterprise compliance before documented implementation and audit.
- Long-context document analysis before chunked, page-indexed ingestion is operational.

## Bottom line

The repository is not a generic AI chatbot project. It already contains the right legal-practice DNA: matter isolation, evidence provenance, official-source verification, privilege, consent, audit, and human supervision. That is a strong foundation for the requested sophisticated legal assistant studio.

However, the repo must now convert its scaffolds and roadmaps into integrated product systems: personalization, ingestion, retrieval, drafting artifacts, collaboration, secure operations, and cross-platform delivery. The next PRD and technical specification should consolidate the broadened studio vision while preserving the existing non-negotiable legal safety gates.
