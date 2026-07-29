# Production Completion Roadmap — BC Legal AI Associate / AI Legal Assistant Studio

**Date:** 2026-07-23  
**Roadmap basis:** `docs/COMPREHENSIVE_SYSTEM_AUDIT_2026-07-23.md`, `docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md`, `docs/AI_LEGAL_ASSISTANT_STUDIO_PRD_SPEC.md`  
**Current verified state:** internal-alpha/prototype foundation with passing diagnostics  
**Target state:** controlled-production, supervised, source-grounded, matter-isolated AI legal assistant studio

## 1. Roadmap control principles

1. **No real-client production before M1/M2 security and provenance gates.**
2. **No court-ready output before M3/M5 citation, authority, procedure, privilege, and human-approval gates.**
3. **No autonomous legal advice, filing, service, settlement, waiver, or significant communication.**
4. **No fine-tuning before official-source retrieval, citation evaluation, and legal golden sets.**
5. **No public demo capability may accept, persist, or process confidential client material.**
6. **Every feature must ship with tests, audit events, permissions, documentation, and rollback posture.**

## 2. Priority and complexity scale

| Label | Meaning |
|---|---|
| P0 | Release blocker / safety-critical / must precede further production expansion |
| P1 | Core production foundation / required for supervised beta |
| P2 | Controlled-production feature / required before broader pilots |
| P3 | Expansion / optimization / post-production enhancement |
| S | Small, localized change |
| M | Moderate subsystem change |
| L | Large cross-module implementation |
| XL | Program-level workstream with multiple epics |

## 3. Milestone overview

| Milestone | Name | Production purpose | Priority | Complexity |
|---|---|---|---:|---:|
| R0 | Stabilization and governance baseline | Keep current foundation green and controlled | P0 | M |
| R1 | Secure identity, matter isolation, and audit | Safe authenticated multi-user base | P0/P1 | XL |
| R2 | Production document ingestion and evidence provenance | Convert records into reliable source-linked facts | P1 | XL |
| R3 | Official legal knowledge, retrieval, and citation verification | Ground law in authoritative sources | P1 | XL |
| R4 | Controlled reasoning, HITL, and AI orchestration | Make AI outputs auditable and supervised | P1 | L/XL |
| R5 | Procedure, deadlines, drafting, and export | Create court/work-product outputs safely | P1/P2 | XL |
| R6 | Personalization, collaboration, and client portal | Turn workbench into team studio | P2 | XL |
| R7 | Platform distribution and local connectors | Deliver secure web/desktop/mobile clients | P2 | L/XL |
| R8 | Evaluation, security, privacy, and pilot hardening | Certify controlled release | P0/P1 | XL |
| R9 | Controlled production operations | Run safely under continuous compliance | P1/P2 | XL |
| R10 | Post-production expansion | Broaden domains, models, integrations | P3 | XL |

## 4. R0 — Stabilization and governance baseline

### R0.1 Keep diagnostics green

- **Priority:** P0
- **Complexity:** M
- **Build:** CI-equivalent checks for `pytest`, Ruff, frontend build, confidential scan, deployment readiness, and HF asset validation.
- **Why:** The audit stabilized the current repo; continued development must not regress foundational safety.
- **Interconnections:** All modules; blocks release packaging and public demos.
- **Prerequisites:** Current passing diagnostics.
- **Acceptance:** CI rejects any change that breaks tests, runtime lint, frontend build, or confidential scan.

### R0.2 Formalize CI workflow

- **Priority:** P0
- **Complexity:** M
- **Build:** GitHub Actions or equivalent workflow for backend tests, frontend build, lint, confidential scan, dependency audit, and artifact checks.
- **Why:** Manual diagnostics are not enough for production development.
- **Interconnections:** Repo governance, release process, branch protection.
- **Prerequisites:** Defined Python/Node versions; secrets-free CI config.
- **Acceptance:** Pull requests cannot merge unless all required checks pass.

### R0.3 Branch protection and release approval

- **Priority:** P0
- **Complexity:** M
- **Build:** Protected `main`, required reviews, CODEOWNERS, signed tags/releases, release checklist, human approval manifest.
- **Why:** Legal AI systems require controlled releases and auditability.
- **Interconnections:** Deployment, Hugging Face publication, installer signing, production rollouts.
- **Prerequisites:** Repository admin access.
- **Acceptance:** Direct pushes to protected branches are blocked; release checklist required.

### R0.4 Product-claim governance

- **Priority:** P0
- **Complexity:** S/M
- **Build:** Automated scan and human review for false claims: production-ready, lawyer, legal advice, E2EE, court-ready, OCR, verified treatment, MFA, etc.
- **Why:** Misstating capabilities creates legal, regulatory, and user-safety risk.
- **Interconnections:** README/docs/UI/public Space/model cards.
- **Prerequisites:** Approved claim vocabulary.
- **Acceptance:** Public-facing changes pass claim-control review.

### R0.5 Dependency and runtime version control

- **Priority:** P1
- **Complexity:** M
- **Build:** Lockfiles, pinned major versions, Python version decision, Node version enforcement, dependency update cadence.
- **Why:** Current environment shows Python 3.14 while project declares >=3.11; test-client warning signals dependency drift.
- **Interconnections:** CI, packaging, tests, deployment.
- **Prerequisites:** Supported runtime matrix.
- **Acceptance:** Reproducible install on supported dev and CI environments.

## 5. R1 — Secure identity, matter isolation, and audit

### R1.1 Production authentication

- **Priority:** P0
- **Complexity:** L
- **Build:** MFA, recovery codes, secure password policies, session expiry/rotation, device management, lockout/rate limiting, secure cookies or hardened token transport.
- **Why:** Real legal data cannot be handled with prototype login/session controls.
- **Interconnections:** Every API route, portal, desktop shell, audit ledger.
- **Prerequisites:** User/org schema finalized; threat model draft.
- **Acceptance:** MFA enforced in production; auth events audited; adversarial auth tests pass.

### R1.2 SSO/OIDC enterprise integration

- **Priority:** P2
- **Complexity:** L
- **Build:** OIDC/SAML-compatible organization SSO, SCIM or user provisioning plan, domain verification, admin controls.
- **Why:** Firms/in-house teams need centralized identity governance.
- **Interconnections:** Org admin, RBAC/ABAC, audit, client portal.
- **Prerequisites:** Production auth architecture.
- **Acceptance:** Pilot org can use SSO with role mapping and audit events.

### R1.3 RBAC/ABAC and ethical walls

- **Priority:** P0/P1
- **Complexity:** XL
- **Build:** Deny-by-default permissions, matter roles, document ACLs, ethical walls, grant expiry, revocation, inherited permissions, portal-limited roles.
- **Why:** Cross-matter leakage is a critical failure in legal systems.
- **Interconnections:** Matters, documents, chats, evidence, citations, tasks, exports, portal, local connector.
- **Prerequisites:** Identity and matter schema.
- **Acceptance:** Cross-matter isolation tests pass; unauthorized objects never appear in API/UI/search/retrieval.

### R1.4 Conflict-checking engine

- **Priority:** P1
- **Complexity:** L
- **Build:** Party/person/entity/address aliases, former-client records, opposing parties, fuzzy matching, waiver records, conflict-review states.
- **Why:** Legal work cannot proceed without conflict controls.
- **Interconnections:** Matter creation, intake, portal, assignments, competency gates.
- **Prerequisites:** Party/entity model.
- **Acceptance:** Matter activation requires conflict check or documented override.

### R1.5 Consent and processing-basis service

- **Priority:** P1
- **Complexity:** L
- **Build:** Purpose/category/model-destination consent, notice versions, withdrawal propagation, derived-data handling, client-visible consent history.
- **Why:** Legal AI processing must distinguish consent, privilege, confidentiality, and retention obligations.
- **Interconnections:** AI orchestration, ingestion, external model routing, portal, audit.
- **Prerequisites:** Identity/matter/portal roles.
- **Acceptance:** Optional processing stops after withdrawal; audit shows why data was processed.

### R1.6 Tamper-evident audit ledger hardening

- **Priority:** P0/P1
- **Complexity:** L
- **Build:** Append-only DB constraints, hash-chain verification, actor/object/event taxonomy, WORM export, immutable replication, audit viewer.
- **Why:** Every sensitive access/output must be defensible.
- **Interconnections:** All modules.
- **Prerequisites:** Event schema and storage strategy.
- **Acceptance:** Audit chain verifies; tamper simulation is detected; release actions are auditable.

### R1.7 Production data store migration

- **Priority:** P1
- **Complexity:** XL
- **Build:** PostgreSQL migration lifecycle, schema versioning, transactional boundaries, connection pooling, seed/migration tests, backup/restore.
- **Why:** SQLite is not the production store for multi-user legal data.
- **Interconnections:** Identity, matters, evidence, citations, audit, tasks, drafts.
- **Prerequisites:** Finalized v1 schema.
- **Acceptance:** Test suite runs against Postgres in CI; backup restore succeeds.

## 6. R2 — Production document ingestion and evidence provenance

### R2.1 Quarantine and file validation

- **Priority:** P1
- **Complexity:** L
- **Build:** Upload quarantine, malware scanning hooks, MIME/type validation, size limits, hash originals, reject/hold/review states.
- **Why:** Legal records may contain malicious or sensitive content and must not be indexed blindly.
- **Interconnections:** Portal upload, local connector, evidence extraction, object storage.
- **Prerequisites:** Object storage and matter ACLs.
- **Acceptance:** No upload becomes searchable before quarantine passes.

### R2.2 Immutable original and derived-layer storage

- **Priority:** P1
- **Complexity:** L
- **Build:** S3-compatible object storage, immutable original buckets, derived text/OCR/embedding layers, versioning, lifecycle policies.
- **Why:** Evidence integrity requires preserving originals separately from processed artifacts.
- **Interconnections:** Evidence, exports, retention, legal holds, audit.
- **Prerequisites:** Storage security/key policy.
- **Acceptance:** Every derived artifact links to original hash/version.

### R2.3 Native text extraction and OCR

- **Priority:** P1
- **Complexity:** XL
- **Build:** PDF/docx/email/text extraction; OCR for scanned PDFs/images; page coordinates; confidence; retry/failure states.
- **Why:** Long legal records must become page-addressable evidence.
- **Interconnections:** Evidence Matrix, retrieval, drafting, citation-to-record linkage.
- **Prerequisites:** Worker queue, object storage, quarantine.
- **Acceptance:** Scanned and native fixtures produce page-indexed text with confidence metadata.

### R2.4 Media transcription

- **Priority:** P2
- **Complexity:** L
- **Build:** Audio/video transcription, timestamps, speaker diarization/review states, original media preservation.
- **Why:** Legal files often include hearings, calls, inspections, recordings.
- **Interconnections:** Evidence timeline, witness prep, contradiction detection.
- **Prerequisites:** Media storage and worker queue.
- **Acceptance:** Transcript spans link to timestamps and require review when confidence is low.

### R2.5 Evidence Matrix persistence

- **Priority:** P1
- **Complexity:** XL
- **Build:** Persistent EvidenceNode store, source spans, relationships, contradiction/support/gap states, human review, concurrency safety.
- **Why:** The evidence engine is what distinguishes the platform from a prompt UI.
- **Interconnections:** Drafting, reasoning, timelines, export manifests, retrieval.
- **Prerequisites:** R2.1–R2.3.
- **Acceptance:** Every finalized factual proposition has source provenance; matrix survives restarts/concurrent edits.

### R2.6 No-truncation long-record processing

- **Priority:** P1
- **Complexity:** L
- **Build:** Chunking, summarization layers, retrieval indexes, record-completeness indicators, no silent context-window truncation.
- **Why:** Legal records exceed model context windows; silent truncation is dangerous.
- **Interconnections:** Chat, drafting, evidence, research.
- **Prerequisites:** Page/span indexing.
- **Acceptance:** UI and API disclose record coverage and missing/unprocessed sections.

## 7. R3 — Official legal knowledge, retrieval, and citation verification

### R3.1 Source registry governance

- **Priority:** P1
- **Complexity:** M/L
- **Build:** Approved sources, source types, official/court/tribunal/secondary classification, update cadence, hash/currency metadata.
- **Why:** AI legal truth must come from governed sources.
- **Interconnections:** Retrieval, citations, drafting, legal tests.
- **Prerequisites:** Knowledgebase schema.
- **Acceptance:** Every authority/source has status, provenance, and update policy.

### R3.2 BC Laws ingestion and point-in-time law

- **Priority:** P1
- **Complexity:** XL
- **Build:** Current/historical statutes/regulations from official BC Laws, effective dates, currency lines, snapshots, change detection.
- **Why:** Statutory errors are high-risk in legal outputs.
- **Interconnections:** Legal tests, drafting, deadlines, citation verification.
- **Prerequisites:** Source registry and storage.
- **Acceptance:** Statutory outputs cite official source, version, effective date, and retrieval timestamp.

### R3.3 Court and tribunal authority ingestion

- **Priority:** P1/P2
- **Complexity:** XL
- **Build:** BCSC/BCCA/SCC/RTB authority ingestion from approved public sources, metadata, court level, decision date, citations, duplicate detection.
- **Why:** Legal research needs case law and tribunal decisions beyond statutes.
- **Interconnections:** BOA builder, research chat, drafting, citation verification.
- **Prerequisites:** Source registry and downloader policy.
- **Acceptance:** Authorities have existence, metadata, source, and binding-weight fields.

### R3.4 Citation verification pipeline

- **Priority:** P1
- **Complexity:** XL
- **Build:** Citation parser, existence check, pinpoint support check, proposition support, jurisdiction/weight, currency, treatment/appellate history.
- **Why:** Court-ready output must not include unsupported or invented citations.
- **Interconnections:** Research, drafting, export manifests, legal tests.
- **Prerequisites:** R3.1–R3.3.
- **Acceptance:** Unverified/rejected/superseded authorities cannot enter court-ready exports.

### R3.5 Hybrid legal retrieval

- **Priority:** P1/P2
- **Complexity:** L/XL
- **Build:** Lexical + vector search, source filtering, matter/source separation, citation-aware retrieval, retrieval evaluation.
- **Why:** Lawyers need reliable recall and precision, not generic semantic guesses.
- **Interconnections:** Research chat, drafting, legal tests, model orchestration.
- **Prerequisites:** pgvector and source corpus.
- **Acceptance:** Retrieval benchmark meets recall/precision thresholds on legal golden queries.

### R3.6 Change alerts and invalidation

- **Priority:** P2
- **Complexity:** L
- **Build:** Source update monitor, affected matter/template/test analysis, stale-output flags, notification workflow.
- **Why:** Legal outputs can become stale when law changes.
- **Interconnections:** Active matters, templates, citations, legal tests, tasks.
- **Prerequisites:** Source versioning.
- **Acceptance:** Changed source triggers affected-object report and blocks stale court-ready use.

## 8. R4 — Controlled reasoning, HITL, and AI orchestration

### R4.1 Unified AI orchestration layer

- **Priority:** P1
- **Complexity:** XL
- **Build:** Request classifier, mode router, tool planner, retrieval selector, safety gates, model routing, response generator, audit events.
- **Why:** Current analysis is deterministic scaffold; production needs structured, controlled AI execution.
- **Interconnections:** Chat, evidence, research, drafting, tasks, settings.
- **Prerequisites:** R1/R2/R3 foundations.
- **Acceptance:** Every AI output records sources, tools, model/policy, gates, and review state.

### R4.2 Model governance and routing

- **Priority:** P1
- **Complexity:** L
- **Build:** Private/local/external model policy, consent checks, token/cost/rate limits, pinned model versions, no confidential public paths.
- **Why:** Legal confidentiality and cost control require model governance.
- **Interconnections:** Consent, privacy, audit, deployment, settings.
- **Prerequisites:** Consent and orchestration layer.
- **Acceptance:** External model call impossible without policy/consent basis and audit event.

### R4.3 LegalTest registry

- **Priority:** P1
- **Complexity:** L
- **Build:** Lawyer-approved legal tests, versioning, jurisdiction/effective date, source links, disable/retire flows, validation tests.
- **Why:** Legal reasoning must not rely on stale or unsupported test definitions.
- **Interconnections:** R3 sources, drafting, reasoning, evaluations.
- **Prerequisites:** Official law source registry.
- **Acceptance:** Legal tests cannot be activated without verified source snapshot and approval.

### R4.4 Human-in-the-loop control plane

- **Priority:** P1
- **Complexity:** L/XL
- **Build:** Approval records, supervisor queues, exception freeze, privilege review, competency gate, two-person review where required.
- **Why:** The system is supervised support, not autonomous practice.
- **Interconnections:** Exports, drafting, privilege, consent, tasks.
- **Prerequisites:** Identity roles and audit ledger.
- **Acceptance:** Critical exceptions freeze outputs until qualified review.

### R4.5 Agent task plans

- **Priority:** P2
- **Complexity:** L
- **Build:** Plan objects, approve/edit/cancel, step audit, scoped tool permissions, external-action hard stops.
- **Why:** Agents can improve productivity only if bounded and auditable.
- **Interconnections:** Automation studio, tasks, export, research.
- **Prerequisites:** Orchestration and HITL.
- **Acceptance:** Agents cannot file, serve, disclose, settle, waive privilege, or communicate externally without separate approval.

## 9. R5 — Procedure, deadlines, drafting, and export

### R5.1 Deterministic deadline engine

- **Priority:** P1
- **Complexity:** XL
- **Build:** Rules by forum/document/service method/start event/deemed receipt/weekends/holidays/extensions/human confirmation.
- **Why:** Deadline errors are critical legal failures.
- **Interconnections:** Intake, tasks, calendar, portal, drafting, post-resolution.
- **Prerequisites:** Official rules/source registry.
- **Acceptance:** 100% pass on critical deadline benchmark fixtures; definitive deadlines require human confirmation.

### R5.2 Procedure engine

- **Priority:** P1/P2
- **Complexity:** XL
- **Build:** BCSC/RTB procedural rules, registry requirements, form versions, filing/service constraints, procedural checklists.
- **Why:** Drafts are not useful if procedurally defective.
- **Interconnections:** Drafting, export, deadlines, legal tests.
- **Prerequisites:** R3 source registry and rule ingestion.
- **Acceptance:** Export readiness includes procedure validation report.

### R5.3 Draft artifact editor and versioning

- **Priority:** P1/P2
- **Complexity:** XL
- **Build:** Side-by-side chat/editor, version history, redlines, comments, paragraph-source links, warnings for unsupported facts/unverified law.
- **Why:** Legal professionals need editable work product, not just chat responses.
- **Interconnections:** Evidence, citations, tasks, approvals, export.
- **Prerequisites:** Evidence/citation provenance.
- **Acceptance:** Draft paragraphs can be traced to evidence/legal sources or marked unsupported.

### R5.4 Template and form library

- **Priority:** P1/P2
- **Complexity:** L
- **Build:** Versioned Form 66/67/32/33/109, RTB forms, memos, affidavits, contracts, letters, BOA/BOD templates.
- **Why:** Drafting must use current correct forms and conventions.
- **Interconnections:** Procedure engine, legal source updates, drafting editor.
- **Prerequisites:** Template governance and source monitoring.
- **Acceptance:** Templates have version, jurisdiction, source, approval, and deprecation status.

### R5.5 Export rendering

- **Priority:** P2
- **Complexity:** XL
- **Build:** DOCX, searchable PDF, PDF/A, package ZIP, indexes, bookmarks, tabs, exhibit schedules, BOA/BOD packages.
- **Why:** Legal work must leave the system in court/firm-ready formats.
- **Interconnections:** Drafts, evidence, citations, privilege, redaction.
- **Prerequisites:** Drafting/procedure/export manifest gates.
- **Acceptance:** Rendered outputs pass visual/regression checks and manifest gates.

### R5.6 Redaction and disclosure controls

- **Priority:** P1/P2
- **Complexity:** L/XL
- **Build:** Redaction suggestions, manual redaction, irreversible output redaction, privilege/PII warnings, disclosure packages.
- **Why:** Accidental disclosure can waive privilege or expose private data.
- **Interconnections:** Ingestion, privilege, export, client portal.
- **Prerequisites:** Document rendering and privilege classification.
- **Acceptance:** Export cannot include flagged privileged/PII material without approval/waiver path.

## 10. R6 — Personalization, collaboration, and client portal

### R6.1 Settings and personalization system

- **Priority:** P2
- **Complexity:** L
- **Build:** User/org/matter profiles for tone, formality, length, language, domain, jurisdiction, output style, model policy.
- **Why:** The studio vision requires customizable workflows.
- **Interconnections:** AI orchestration, drafting, UI, admin.
- **Prerequisites:** Identity and policy compiler.
- **Acceptance:** Settings affect output style but cannot disable legal gates.

### R6.2 Shared workspaces and collaboration

- **Priority:** P2
- **Complexity:** XL
- **Build:** Matter teams, tasks, assignments, comments, annotations, activity feed, notifications, approval queues.
- **Why:** Legal work is collaborative and review-driven.
- **Interconnections:** Matters, drafts, evidence, portal, audit.
- **Prerequisites:** RBAC/ABAC and audit events.
- **Acceptance:** Role-limited collaborators can work without cross-matter leakage.

### R6.3 Client portal

- **Priority:** P2
- **Complexity:** XL
- **Build:** Client login, dashboard, status, tasks, guided upload, document previews, consent center, messages, notifications.
- **Why:** Clients need secure participation without seeing internal work product.
- **Interconnections:** Auth, matter ACLs, quarantine, messaging, consent.
- **Prerequisites:** R1/R2 foundations.
- **Acceptance:** Portal user sees only explicitly authorized materials; uploads quarantine.

### R6.4 Secure messaging

- **Priority:** P2
- **Complexity:** L/XL
- **Build:** Matter-scoped messages, attachments, read receipts, approval-before-send, accurate encryption model, privilege prompts.
- **Why:** Communication is legally significant and must be controlled.
- **Interconnections:** Portal, audit, privilege, tasks.
- **Prerequisites:** Encryption architecture decision.
- **Acceptance:** System does not falsely claim E2EE where server-side AI reads content.

### R6.5 Accessibility and localization

- **Priority:** P2
- **Complexity:** L
- **Build:** WCAG-aligned UI, keyboard/screen-reader tests, responsive mobile, plain-language mode, multilingual output/translation workflow.
- **Why:** Legal access and usability require inclusive design.
- **Interconnections:** UI, portal, drafting, settings.
- **Prerequisites:** UX design system.
- **Acceptance:** Accessibility audit passes target standard.

## 11. R7 — Platform distribution and local connectors

### R7.1 Web/PWA hardening

- **Priority:** P2
- **Complexity:** L
- **Build:** Environment-aware builds, CSP, secure cookies, service-worker cache policy, offline warning, deployment pipeline.
- **Why:** Web app must not leak sensitive data or serve stale legal state silently.
- **Interconnections:** Frontend, auth, legal source updates.
- **Prerequisites:** Production hosting architecture.
- **Acceptance:** PWA security review passes; offline behavior is safe.

### R7.2 Tauri desktop packaging

- **Priority:** P2
- **Complexity:** L
- **Build:** Signed Windows/macOS installers, auto-update, OS credential storage, logging policy, distribution docs.
- **Why:** Desktop workbench is primary installable surface.
- **Interconnections:** Local connector, auth, update strategy.
- **Prerequisites:** Code-signing certificates and release pipeline.
- **Acceptance:** Signed installer installs/updates cleanly in pilot environment.

### R7.3 Approved-folder Windows connector

- **Priority:** P2
- **Complexity:** XL
- **Build:** User-selected folders only, inventory, preview, exclusion list, consent, privilege classification, dedupe, local audit, revocation, secure upload/local OCR.
- **Why:** Whole-PC indexing is unsafe; controlled local import is valuable.
- **Interconnections:** Ingestion, portal, object storage, privilege, audit.
- **Prerequisites:** R1/R2 security and provenance.
- **Acceptance:** Connector cannot scan outside approved folders and logs every import.

### R7.4 Mobile shells

- **Priority:** P3
- **Complexity:** XL
- **Build:** Android/iOS Tauri or alternative mobile shell, secure storage, camera upload, push notifications, responsive UX.
- **Why:** Client and field evidence workflows benefit from mobile.
- **Interconnections:** Portal, upload, notifications.
- **Prerequisites:** Portal and PWA maturity.
- **Acceptance:** Mobile beta passes platform security review.

## 12. R8 — Evaluation, security, privacy, and pilot hardening

### R8.1 Legal golden-set evaluations

- **Priority:** P0/P1
- **Complexity:** XL
- **Build:** Golden matters for tenancy, JR, civil procedure, evidence, remedies, adverse authorities, deadlines, drafting.
- **Why:** Legal AI needs domain-specific evaluation, not just unit tests.
- **Interconnections:** R3/R4/R5.
- **Prerequisites:** Lawyer-reviewed fixtures.
- **Acceptance:** ≥95% overall, 100% on critical safety controls.

### R8.2 Hallucination and citation red team

- **Priority:** P0/P1
- **Complexity:** L
- **Build:** Fake citations, stale law, wrong jurisdiction, unsupported propositions, prompt-injected authorities.
- **Why:** Citation hallucination is a core legal AI risk.
- **Interconnections:** Retrieval, citation verification, drafting.
- **Prerequisites:** Citation pipeline and evaluation harness.
- **Acceptance:** Court-ready outputs contain zero unverified citations.

### R8.3 Cross-matter leakage and authorization abuse tests

- **Priority:** P0
- **Complexity:** L
- **Build:** Adversarial ACL tests for API, UI, retrieval, search, tasks, exports, chats, local connector.
- **Why:** One client seeing another client’s material is catastrophic.
- **Interconnections:** All matter-scoped modules.
- **Prerequisites:** RBAC/ABAC implementation.
- **Acceptance:** Zero cross-matter leakage in red-team suite.

### R8.4 Security program

- **Priority:** P0/P1
- **Complexity:** XL
- **Build:** Threat model, dependency/SBOM scanning, secrets management, pen test, incident-response exercise, DR test, monitoring/alerting.
- **Why:** Production legal systems require mature security operations.
- **Interconnections:** Deployment, storage, auth, portal, connectors.
- **Prerequisites:** Production architecture.
- **Acceptance:** No critical security findings before release.

### R8.5 Privacy and regulatory review

- **Priority:** P0/P1
- **Complexity:** L/XL
- **Build:** Privacy impact assessment, vendor/model review, data residency, client disclosures, retention/destruction review, Law Society/sandbox path where applicable.
- **Why:** Legal AI deployment has regulatory and professional obligations.
- **Interconnections:** Product claims, consent, external models, portal, operations.
- **Prerequisites:** Defined pilot scope.
- **Acceptance:** Pilot legal basis and disclosures approved.

### R8.6 Load, performance, and reliability benchmarks

- **Priority:** P1/P2
- **Complexity:** L
- **Build:** Ingestion throughput, OCR latency, retrieval latency, concurrent users, memory profiling, queue backpressure, DB index review.
- **Why:** Large legal records stress memory, queues, storage, and retrieval.
- **Interconnections:** R2/R3/R4/R5.
- **Prerequisites:** Production-like environment.
- **Acceptance:** Benchmarks meet defined SLOs under pilot load.

## 13. R9 — Controlled production operations

### R9.1 Pilot charter and scope controls

- **Priority:** P0/P1
- **Complexity:** M/L
- **Build:** Pilot scope, permitted users, legal domains, matter limits, escalation/rollback criteria, client disclosures.
- **Why:** Controlled production must be narrow and governed.
- **Interconnections:** Security, privacy, support, release management.
- **Prerequisites:** R8 approvals.
- **Acceptance:** Formal pilot approval signed before real-client data.

### R9.2 Production observability

- **Priority:** P1
- **Complexity:** L
- **Build:** Logs, metrics, traces, audit dashboards, alerting, model/tool usage dashboards, source-update monitoring.
- **Why:** Operations must detect failures, abuse, stale law, and performance degradation.
- **Interconnections:** All production services.
- **Prerequisites:** Deployment platform.
- **Acceptance:** On-call can diagnose incidents without exposing privileged content.

### R9.3 Backup, restore, retention, and legal holds

- **Priority:** P1
- **Complexity:** XL
- **Build:** Encrypted backups, restore drills, retention schedules, legal holds, destruction workflow for originals/derivatives/indexes/backups.
- **Why:** Legal records require durable preservation and controlled destruction.
- **Interconnections:** Storage, evidence, audit, portal, post-resolution.
- **Prerequisites:** Storage architecture and policy review.
- **Acceptance:** Restore and destruction tests pass; legal holds block deletion.

### R9.4 Support and incident response

- **Priority:** P1
- **Complexity:** L
- **Build:** Support process, severity levels, breach response, privilege incident workflow, user training, release rollback.
- **Why:** Legal AI incidents need disciplined handling.
- **Interconnections:** Audit, security, privacy, client communications.
- **Prerequisites:** IR plan and trained owners.
- **Acceptance:** Tabletop exercise completed before controlled production.

### R9.5 Continuous legal-source maintenance

- **Priority:** P1
- **Complexity:** L
- **Build:** Scheduled source updates, human review of major changes, affected-matter alerts, template/test invalidation.
- **Why:** Law changes continuously.
- **Interconnections:** R3/R4/R5.
- **Prerequisites:** Source registry and alerting.
- **Acceptance:** Source currency dashboard is monitored and stale outputs are blocked.

## 14. R10 — Post-production expansion

### R10.1 Domain expansion

- **Priority:** P3
- **Complexity:** XL
- **Build:** Add corporate, IP, environmental, regulatory, and other jurisdictions only after source/eval framework proves reliable.
- **Why:** Studio vision includes multiple legal domains, but expansion without source governance creates risk.
- **Interconnections:** Research, templates, legal tests, evaluations.
- **Prerequisites:** R3/R8 maturity.
- **Acceptance:** Each domain has sources, tests, templates, evaluation fixtures, and reviewer approval.

### R10.2 Advanced model comparison and local models

- **Priority:** P3
- **Complexity:** L/XL
- **Build:** Model selector, model comparison, local Ollama/private inference, cost dashboards, quality evals.
- **Why:** Power users need model flexibility within legal controls.
- **Interconnections:** Consent, model governance, orchestration.
- **Prerequisites:** R4/R8.
- **Acceptance:** Model choice never bypasses source/citation/privilege gates.

### R10.3 Browser/email/calendar integrations

- **Priority:** P3
- **Complexity:** XL
- **Build:** Outlook/Gmail/calendar connectors, browser extension, attachment review, task extraction, approval-before-send.
- **Why:** Legal workflows happen across communication and scheduling tools.
- **Interconnections:** Messaging, tasks, privilege, deadlines.
- **Prerequisites:** Security review and OAuth governance.
- **Acceptance:** Integrations are scoped, revocable, audited, and cannot send legally significant messages autonomously.

### R10.4 Advanced analytics and reporting

- **Priority:** P3
- **Complexity:** L
- **Build:** Matter health dashboards, workload reports, source-currency reports, evaluation dashboards, cost/latency reports.
- **Why:** Firms need operational visibility.
- **Interconnections:** Audit, observability, tasks, evaluations.
- **Prerequisites:** Production telemetry.
- **Acceptance:** Reports reveal operational trends without exposing unauthorized matter content.

## 15. Cross-cutting non-functional requirements checklist

| Requirement | Must be completed by | Key acceptance |
|---|---|---|
| Security hardening | R8 before pilot | No critical findings; threat model and pen test complete |
| Privacy governance | R8 before pilot | PIA/vendor review/client disclosures approved |
| Performance benchmarks | R8 before pilot | Defined SLOs met under pilot load |
| Scalability foundation | R1/R2/R3/R9 | Postgres/object store/Redis workers operational |
| Reliability and DR | R9 before controlled production | Restore/IR/DR tests pass |
| Accessibility | R6/R8 | WCAG target audit passes |
| Documentation | Every milestone | User/admin/developer/release docs updated |
| Testing coverage | Every milestone | Unit/integration/e2e/security/legal evals pass |
| Deployment readiness | R7/R8/R9 | Signed builds, secure envs, monitored releases |
| Legal compliance | R8/R9 | Supervision/regulatory/pilot scope approved |

## 16. Immediate next sprint recommendation

### Sprint P0-Next — Stabilize and institutionalize audit results

1. Commit or review the current remediation changes.
2. Add CI workflows for tests, lint, frontend build, scans, and readiness validation.
3. Lock runtime versions and dependency policy.
4. Migrate remaining legacy `_user` route usage toward `CurrentUser` dependency gradually.
5. Add route tests for workspace analyzer citation regex and conversation helper aliasing to prevent regression.
6. Add frontend smoke/e2e test for the conversational workspace shell.
7. Add product-claim scan for public docs/UI.
8. Create GitHub milestones/issues from this roadmap.

**Definition of done:** All diagnostics pass in CI; roadmap issues are created; branch protection prevents regression; public claims remain aligned with implemented capability.

## 17. Final production-readiness gate

The system becomes a production candidate only when all of the following are true:

- Zero known cross-matter leakage.
- Zero unverified citations in court-ready output.
- Zero unsupported facts in finalized work product.
- Zero privilege-gate bypasses.
- 100% critical deadline benchmark pass rate.
- 100% page/source provenance for finalized factual propositions.
- ≥95% legal golden-set pass rate and 100% on critical controls.
- No critical security findings.
- Backup restore tested.
- Privacy/regulatory review approved.
- Supervising-user training complete.
- Pilot scope and rollback criteria approved.
- Public and client-facing claims match implemented functionality.

## 18. Bottom line

The audited system is now stable enough for continued internal-alpha development, but the route to production is still a multi-milestone engineering, legal, security, and governance program. The correct next focus is not feature spectacle. It is M1–M3 production substrate: secure identity/isolation, document provenance, and official legal-source verification. Everything else depends on that foundation.
