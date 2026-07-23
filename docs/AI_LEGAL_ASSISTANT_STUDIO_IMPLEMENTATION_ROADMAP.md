# AI Legal Assistant Studio — Implementation Roadmap and Milestones

**Product family:** BC Legal AI Associate  
**Document role:** Practical implementation roadmap for evolving the current repository into the broader AI legal assistant studio described in `AI_LEGAL_ASSISTANT_STUDIO_PRD_SPEC.md`.  
**Date:** 2026-07-23  
**Status:** Planning artifact; subordinate to existing legal/safety gates in `docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md`.

## 1. Roadmap principle

The studio vision must be built in dependency order. A polished AI interface must not outrun the legal safety substrate.

The product may look like ChatGPT, Claude, Monica, Copilot, or Kimi at the interface layer, but it must behave like a supervised legal-work system underneath:

```text
Identity + matter isolation
        ↓
Consent + privilege + audit
        ↓
Document ingestion + evidence provenance
        ↓
Official legal retrieval + citation verification
        ↓
Reasoning + drafting + automation
        ↓
Collaboration + client portal
        ↓
Security/legal evaluation + controlled release
```

## 2. Release sequence overview

| Release | Name | Outcome | Real-client suitability |
|---|---|---|---|
| R0 | Repository and safety stabilization | Known defects and public-data risks addressed | No |
| R1 | Secure workspace foundation | Authenticated synthetic/internal matter workspace | No, except synthetic/internal testing |
| R2 | Document intelligence MVP | Quarantine, extraction, page-level provenance, evidence nodes | Limited internal supervised testing |
| R3 | Verified research MVP | Official-source registry, citation verification, retrieval snapshots | Limited internal supervised testing |
| R4 | Drafting studio MVP | Source-linked drafts, artifact editor, approval gates | Supervised pilot candidate after security review |
| R5 | Personalization and workflow studio | Settings, modes, task automation, agent plans | Supervised beta candidate |
| R6 | Collaboration and client portal | Shared workspaces, tasks, annotations, portal, messages | Controlled pilot candidate |
| R7 | Production hardening | Eval, privacy, security, threat model, pilot governance | Production candidate |
| R8 | Controlled production | Narrow approved legal-work deployments | Controlled production only |

## 3. R0 — Repository and safety stabilization

### Objective

Stabilize the current codebase before expanding features, and ensure demos cannot be mistaken for production legal capability.

### Scope

- Fix immediate code defects observed in audit.
- Confirm public demo restrictions.
- Confirm synthetic-data-only behavior for public surfaces.
- Run tests and confidential-data scans.
- Keep product status documents honest and current.

### Key tasks

1. Add missing regex import in `backend/api/platform_routes.py` if still absent.
2. Fix frontend `verifyCitation` API payload in `apps/platform-ui/src/lib/api.ts`.
3. Add or update tests for `/v1/platform/workspace/analyze` citation-pattern handling.
4. Add frontend type checks / build verification for API client.
5. Confirm public demo mode blocks live identifiers and real-client content.
6. Ensure README, `PRODUCT_STATUS.md`, and public surfaces do not claim unshipped studio features.

### Exit gate

- Backend tests pass.
- Frontend build/type checks pass.
- Confidential scan passes.
- Public demo is synthetic-only.
- No court-ready or autonomous legal advice claims appear in public UI.

## 4. R1 — Secure workspace foundation

### Objective

Create a stable authenticated matter workspace suitable for synthetic/internal alpha usage.

### Scope

- Identity, users, organizations, sessions.
- Matter creation and ACL enforcement.
- Persistent conversations.
- Basic workspace UI connected to real authenticated matters, not demo data.
- Audit logging for matter and conversation events.
- Basic settings profile scaffold.

### Backend epics

- Harden `/v1/platform/auth/*` flows.
- Add MFA-ready architecture, even if initially disabled in local dev.
- Enforce matter access on all matter-scoped endpoints.
- Persist conversations, messages, modes, and selected matter context.
- Add initial `/v1/platform/settings/*` for user/org/matter defaults.
- Log audit events for login, matter creation, conversation creation, message creation, and settings change.

### Frontend epics

- Auth screens.
- Matter picker connected to backend.
- Conversation list and history.
- Mode selector connected to conversation state.
- Remove hard dependency on demo matter data for authenticated mode.
- Add settings shell: tone, verbosity, language, legal domain, jurisdiction.

### Exit gate

- Authenticated user can create/select a matter.
- Matter chat cannot access other matters.
- Conversation history persists across refresh.
- Settings save and load.
- All matter access is audited.

## 5. R2 — Document intelligence MVP

### Objective

Enable controlled document ingestion and evidence provenance without relying on a single prompt context window.

### Scope

- Quarantine upload pipeline.
- Immutable originals.
- Text extraction for supported files.
- OCR integration plan and first supported OCR path.
- Page-level indexing.
- EvidenceNode persistence.
- Human review states.

### Backend epics

- Implement `/v1/platform/documents/*` upload, quarantine, status, and retrieval endpoints.
- Store originals in object storage or local development equivalent.
- Hash every original.
- Extract text and split into page/span records.
- Persist document pages/spans.
- Create evidence nodes from selected spans.
- Add document classification and sensitivity placeholders.
- Add duplicate/version detection basics.

### Frontend epics

- Upload panel.
- Quarantine status display.
- Document viewer with page/spans.
- Evidence extraction UI.
- Evidence matrix table.
- Low-confidence/human-review indicators.

### Exit gate

- Uploaded documents enter quarantine before indexing.
- Originals are immutable and hash-identified.
- Extracted text is page/span addressable.
- Evidence nodes link to exact source locations.
- No record is silently truncated to fit a chat prompt.

## 6. R3 — Verified research MVP

### Objective

Move from safe triage to verified legal research primitives.

### Scope

- Source registry.
- Official-source retrieval for priority BC materials.
- Citation parsing and verification.
- Legal-source snapshots.
- Research mode UI.

### Backend epics

- Expand source registry.
- Implement official-source ingestion/update jobs for priority statutes/regulations/rules.
- Support point-in-time source metadata.
- Persist authority records and citations.
- Verify citation existence and known jurisdiction/weight.
- Add citation status values: VERIFIED, PROVISIONAL, REJECTED, STALE, UNSUPPORTED.
- Lock source snapshots for draft/export workflows.

### Frontend epics

- Research mode search UI.
- Citation verification panel.
- Source card viewer.
- Snapshot/version display.
- Court-ready blockers for unverified authorities.

### Exit gate

- Research responses identify source status.
- Citations can be verified or rejected with reasons.
- Court-ready output cannot include rejected/unverified authorities.
- BC statute citations use official-source verification workflow.

## 7. R4 — Drafting studio MVP

### Objective

Create the first source-linked legal drafting environment.

### Scope

- Draft artifact model.
- Side-by-side chat + editor.
- Version history.
- Unsupported fact and unverified citation warnings.
- Approval-gated exports.

### Backend epics

- Add `DraftArtifact` and `DraftVersion` persistence.
- Generate draft skeletons from approved templates.
- Link draft paragraphs to evidence nodes and citation verifications.
- Add export manifests with evidence/citation/privilege/procedure/human approval fields.
- Add DOCX and searchable PDF rendering path for initial document types.

### Frontend epics

- Draft editor panel.
- Version history view.
- Inline warnings for unsupported facts and citations.
- Source/citation side panel.
- Export readiness checklist.

### Initial drafting targets

1. Legal memo.
2. Demand/response letter.
3. Affidavit outline and exhibit schedule.
4. RTB evidence summary.
5. Judicial-review petition scaffold.
6. Contract clause risk report.

### Exit gate

- Drafts persist and version correctly.
- Draft statements link to evidence/citation records where required.
- Unsupported facts and unverified citations are visibly blocked or warned.
- Export requires approval manifest.

## 8. R5 — Personalization and workflow studio

### Objective

Add the customizable studio experience while preserving non-overridable safety gates.

### Scope

- User/org/matter settings.
- Output style profiles.
- Legal-domain profiles.
- Language preferences.
- Agent task planning.
- Workflow automation panel.

### Backend epics

- Implement settings hierarchy: system defaults → org defaults → user defaults → matter overrides → task-specific options.
- Add safe prompt-policy compiler that translates settings into AI instructions without disabling gates.
- Add automation plan objects.
- Add approval-gated agent execution records.
- Add task generation from chat/draft/document events.

### Frontend epics

- Settings center.
- Style profile editor.
- Domain focus selector.
- Language/output controls.
- Agent plan viewer with approve/edit/cancel.
- Task automation panel.

### Exit gate

- Users can customize tone, formality, response length, language, domain, and output format.
- Settings affect responses/drafts in permitted ways.
- Settings cannot disable citation, evidence, privilege, procedure, or approval gates.
- Agent plans are explicit and auditable.

## 9. R6 — Collaboration and client portal

### Objective

Turn the studio into a team legal-work platform.

### Scope

- Shared matter workspaces.
- Task assignment.
- Comments and annotations.
- Approval queues.
- Client portal basics.
- Secure messaging posture.
- Notifications.

### Backend epics

- Add task assignment, comments, annotations, and notifications.
- Add approval queue by matter/user/role.
- Add portal-scoped access roles.
- Add secure messaging model with accurate encryption claims.
- Add client upload flow that always enters quarantine.
- Add consent-center views and history.

### Frontend epics

- Team task board.
- Annotation UI.
- Approval queue.
- Activity feed.
- Client portal dashboard.
- Guided upload.
- Messaging UI.
- Consent center.

### Exit gate

- Users only see matter materials they are authorized to see.
- Tasks and approvals are auditable.
- Client uploads enter quarantine.
- Messaging security claims match technical reality.
- Portal users cannot access internal-only work product unless expressly shared.

## 10. R7 — Production hardening

### Objective

Prepare for controlled real-world pilots.

### Scope

- Legal evaluation suite.
- Security testing.
- Privacy impact assessment.
- Threat model.
- Backup/restore.
- Incident response.
- Accessibility audit.
- Pilot governance.

### Key workstreams

1. **Legal evaluations**
   - Golden matters.
   - Citation hallucination tests.
   - Deadline benchmark fixtures.
   - Evidence provenance coverage tests.
   - Privilege red-team tests.

2. **Security evaluations**
   - Cross-matter isolation tests.
   - Prompt-injection testing.
   - RBAC/ABAC tests.
   - Penetration test.
   - Secrets and dependency review.

3. **Privacy/compliance**
   - Privacy impact assessment.
   - Vendor/model review.
   - Data retention and deletion validation.
   - Client disclosure review.
   - Supervising-user training materials.

4. **Reliability**
   - Backup restore tests.
   - Disaster recovery exercise.
   - Worker failure and retry tests.
   - Audit-ledger verification.

### Exit gate

- Zero known cross-matter leakage.
- Zero critical security findings.
- No citation-gate bypass.
- No privilege-gate bypass.
- Backup restore succeeds.
- Golden-set evaluation passes.
- Pilot scope and legal authorization are formally approved.

## 11. R8 — Controlled production

### Objective

Launch narrowly scoped production deployments with continuous compliance.

### Scope

- Approved users only.
- Approved legal domains only.
- Monitored model/tool use.
- Ongoing source updates.
- Ongoing legal evaluation.
- Incident response and support operations.

### Production controls

- Formal release review.
- Pilot/production scope document.
- Supervising lawyer or authorized legal-service framework where required.
- Client disclosures.
- Support and escalation protocols.
- Monitoring and audit reviews.
- Scheduled security updates.
- Legal-source currency checks.
- Retention and legal hold operations.

### Exit / continuation gate

Controlled production continues only if:

- Critical incidents are addressed.
- Legal-source updates remain current.
- Evaluation scores stay within thresholds.
- Security posture remains acceptable.
- Human supervision and regulatory boundaries remain valid.

## 12. Cross-cutting workstreams

These run across releases but must respect milestone dependencies.

### 12.1 AI and orchestration

- Request classification.
- Tool routing.
- Retrieval orchestration.
- Prompt-policy compiler.
- Source-grounded response generation.
- Agent planning and execution logs.
- Model cost/rate controls.
- Local/private model support.

### 12.2 UI/UX

- Three-panel workspace.
- Side-by-side drafting.
- Evidence/citation work panel.
- Settings center.
- Accessibility.
- Responsive PWA.
- Tauri desktop/mobile shells.

### 12.3 Data and infrastructure

- PostgreSQL migrations.
- pgvector indexes.
- Object storage.
- Redis queues.
- Background workers.
- Observability.
- Backup/restore.

### 12.4 Legal domain expansion

Do not expand legal domains faster than the source and evaluation systems can support.

Recommended order:

1. BC residential tenancy / RTB and judicial review continuation, because repo already has domain scaffolding.
2. General BC civil litigation drafting/research support.
3. Contract review and corporate-commercial document analysis.
4. Regulatory/compliance tracking.
5. Additional jurisdictions only after source, citation, and evaluation frameworks are proven.

## 13. Suggested first implementation sprint

### Sprint S1 — Stabilize workspace scaffold

**Goal:** Convert the current scaffold into a reliable internal-alpha baseline.

Tasks:

1. Fix backend `re` import issue in workspace analysis route.
2. Fix frontend citation verification payload bug.
3. Add backend tests for workspace analyze route.
4. Add frontend build/type-check verification.
5. Add settings schema stub and API route.
6. Add authenticated matter selection to workspace UI or explicitly separate demo mode from authenticated mode.
7. Document public-demo limitations in UI text.

Definition of done:

- `pytest` passes.
- Frontend build passes.
- Workspace analyze route handles citation-like text without server error.
- Citation verify API client sends correct payload.
- Demo mode is visibly synthetic and non-production.

## 14. Milestone dependency rules

- R1 must precede real matter collaboration.
- R2 must precede document-grounded drafting.
- R3 must precede court-ready legal propositions.
- R4 must precede production exports.
- R5 personalization cannot override R1–R4 gates.
- R6 portal must not expose real-client material before R1/R2 security and provenance gates pass.
- R7 must precede controlled real-client release.

## 15. Summary

The roadmap transforms the repository from a supervised BC legal workbench prototype into a broader legal assistant studio in a controlled sequence. The near-term priority is not to add flashy agent behavior; it is to stabilize the authenticated workspace, ingestion, provenance, official-source retrieval, citation verification, and drafting artifacts that make associate-level legal AI defensible.
