# AI Legal Assistant Studio — Product Requirements and Technical Specification

**Product family:** BC Legal AI Associate  
**Document role:** Consolidated PRD + technical specification for the broader AI-powered legal assistant studio vision  
**Status:** Planning / target architecture  
**Date:** 2026-07-23  
**Related docs:**

- `docs/PRODUCT_DESCRIPTION.md`
- `docs/CONVERSATIONAL_WORKSPACE_SPEC.md`
- `PRODUCT_STATUS.md`
- `docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md`
- `docs/DATA_MODEL_AND_EVIDENCE_SCHEMA.md`
- `docs/PRODUCT_VISION_REPO_AUDIT.md`

## 1. Product summary

BC Legal AI Associate will evolve into a sophisticated, customizable, AI-powered legal assistant studio for supervised legal work. The studio combines conversational AI, document drafting, legal research, evidence analysis, task automation, collaboration, and secure matter management in a single matter-scoped workspace.

The product is inspired by modern AI assistants such as ChatGPT, Claude, Monica, Copilot, and Kimi, but it is not a generic chatbot. It is a legal-work operating environment with hard controls for matter isolation, privilege, consent, citation verification, evidence provenance, deadline confirmation, and human approval.

The platform must never be marketed or operated as an autonomous lawyer. It supports legal professionals, authorized legal-service providers, supervised staff, and approved self-represented workflows, subject to jurisdictional and regulatory limits.

## 2. Product goals

### 2.1 Primary goals

1. **Increase legal drafting speed without weakening verification.**
   - Produce contracts, pleadings, affidavits, submissions, memos, correspondence, court forms, tribunal materials, and compliance documents from verified matter facts and approved legal sources.

2. **Make legal research source-grounded and auditable.**
   - Retrieve statutes, regulations, tribunal rules, court rules, cases, policy materials, and forms from approved sources.
   - Verify citations, pinpoints, treatment, point-in-time law, jurisdiction, and binding weight.

3. **Transform large legal records into usable evidence intelligence.**
   - Ingest lengthy case files, contracts, scanned records, transcripts, emails, photos, audio, and video.
   - Extract facts, allegations, issues, contradictions, timelines, clauses, risks, and evidentiary gaps with page/paragraph/timestamp provenance.

4. **Provide a customizable AI studio experience.**
   - Allow users and organizations to configure tone, formality, verbosity, language, legal domain, output format, model/tool routing, and workspace defaults while preserving mandatory legal gates.

5. **Support legal-team collaboration.**
   - Provide shared matter workspaces, task assignment, annotations, document version history, approval workflows, and audit visibility.

6. **Protect confidentiality and professional obligations.**
   - Enforce matter isolation, RBAC/ABAC, ethical walls, consent controls, privilege screens, audit logging, retention, legal holds, and controlled external output.

### 2.2 Non-goals for V1

The V1 studio will not provide:

- Autonomous legal advice to the public.
- Automatic filing, service, settlement, negotiation, privilege waiver, or legally significant communications.
- Whole-computer indexing.
- Fine-tuned legal model weights before RAG, citation, and evaluation gates are mature.
- Unqualified claims of end-to-end encryption where server-side AI processing requires decrypted content.
- Public real-client intake before matter isolation and security gates pass.

## 3. Target users

| User type | Needs | Controls |
|---|---|---|
| Lawyers | Research, drafting, review, delegation, approval, matter oversight | Competency gate, audit trail, approval workflows |
| Paralegals / legal assistants | Intake, document organization, draft preparation, task management | Role-limited access, supervising-lawyer approval |
| In-house legal teams | Contract review, regulatory tracking, collaborative workspaces | Org admin, policy profiles, SSO/RBAC |
| Authorized advocates / clinics | Guided workflows, forms, evidence packages | Scope limits, supervision/authorization controls |
| Self-represented users, where permitted | Plain-language summaries, evidence organization, procedural support | Legal information boundary, no representation claims |
| Clients / witnesses | Secure uploads, messages, tasks, status, consent controls | Portal-limited access, consent, audit |

## 4. Core product surfaces

### 4.1 Conversational workspace

The primary interface is a three-panel conversational legal workspace:

```text
LEFT SIDEBAR              MAIN CONVERSATION              WORK PANEL
Matters                   Chat / voice / files           Sources
Projects                  Agent plans                    Evidence
Agents                    Safety warnings                Drafts
Documents                 Approvals                      Timeline
Calendar                  Citations                      Tasks
Settings                  Composer                       Audit
```

Required conversation types:

- General Chat — no automatic confidential matter access.
- Matter Chat — locked to one matter ACL.
- Document Chat — selected documents with page/timestamp citations.
- Research Chat — official sources and citation verification.
- Drafting Chat — live artifact editor beside chat.
- Agent Task Chat — plan-based automation with approve/edit/cancel controls.

### 4.2 Drafting studio

The drafting environment must support:

- Side-by-side chat and document editor.
- Draft artifact creation from matter facts, evidence, legal tests, and templates.
- Redlines, comments, annotations, and version history.
- Style controls: tone, formality, brevity, audience, jurisdiction, language.
- Clause extraction and clause comparison for contracts.
- Unsupported-fact highlighting.
- Unverified-citation blocking.
- Privilege/procedure/export gates.
- Export to DOCX, searchable PDF, PDF/A, and package ZIP.

Initial priority document types:

1. Legal memoranda.
2. Correspondence and demand letters.
3. Affidavits and exhibit schedules.
4. RTB materials.
5. Judicial-review petition scaffolds and stay materials.
6. Written submissions / briefs.
7. Contract review summaries and clause-risk reports.
8. Books of Authorities / Books of Documents.

### 4.3 Research studio

The research module must:

- Search approved legal sources.
- Retrieve current and historical statutes/regulations.
- Support point-in-time law.
- Verify citation existence, pinpoint, proposition support, jurisdiction, and binding weight.
- Detect superseded authority, negative treatment, and unresolved treatment status.
- Distinguish official, authoritative, persuasive, secondary, and unverified sources.
- Block court-ready exports containing unverified or rejected authorities.

BC statutory text must be verified against the official BC Laws portal. Judicial authorities must be validated by existence, court level, citation, pinpoint support, treatment, and currency.

### 4.4 Document and evidence intelligence

The ingestion and evidence system must:

- Quarantine uploads before indexing.
- Preserve immutable originals.
- Extract text from native files.
- OCR scanned files.
- Extract metadata and EXIF where permitted.
- Split records into page/paragraph/timestamp-addressable units.
- Deduplicate while preserving versions.
- Classify document type and sensitivity.
- Screen for privilege/confidentiality.
- Extract facts, allegations, admissions, issues, dates, witnesses, entities, clauses, risks, and obligations.
- Link every material proposition to source location.
- Maintain an Evidence Matrix with support, contradiction, confidence, and review status.

The platform must not rely on a single long-context prompt as the source of truth. Long-context behavior must be implemented through durable indexing, retrieval, provenance, and summarization pipelines.

### 4.5 Automation studio

Automation must be plan-based and approval-gated.

Example workflows:

- Contract review checklist.
- Clause extraction and risk report.
- Compliance obligation tracker.
- Deadline calculation and reminder draft.
- Evidence gap report.
- Hearing preparation outline.
- Citation verification batch.
- Court package assembly.
- Post-resolution compliance monitoring.

Agents may prepare, classify, draft, summarize, compare, and propose actions. Agents may not autonomously file, serve, disclose, settle, waive privilege, send legally significant communications, or provide final legal advice.

### 4.6 Collaboration studio

The collaboration layer must support:

- Shared matter workspaces.
- User roles and team membership.
- Task assignment, due dates, status, priority, and dependencies.
- Contextual annotations on documents, evidence nodes, citations, and drafts.
- Document version history.
- Approval queues.
- Notifications.
- Activity and audit timelines.
- Matter-specific discussion threads.

### 4.7 Settings and personalization

The studio requires first-class personalization, with safe defaults and non-overridable gates.

Settings categories:

| Category | Examples |
|---|---|
| Response style | Tone, formality, directness, verbosity, structure |
| Language | UI language, output language, translation handling |
| Legal domain | Tenancy, civil litigation, corporate, IP, environmental, regulatory, general |
| Jurisdiction | BC default, Canada federal, other supported jurisdictions as enabled |
| Drafting defaults | Preferred templates, citation style, argument style, signature blocks |
| Research defaults | Source priority, court hierarchy, date range, treatment strictness |
| Automation defaults | Require confirmation at each step, batch size, notification preferences |
| Model/tool routing | Private model only, external model allowed with consent, local model preferred |
| Privacy | Redaction defaults, external processing restrictions, retention preferences |
| Accessibility | Font scale, contrast, screen-reader mode, simplified language |

Mandatory legal controls cannot be disabled by personalization settings.

## 5. Legal and compliance requirements

### 5.1 Mandatory legal boundary

The product must state and enforce:

- The AI is not a lawyer.
- The system does not create a solicitor-client relationship by itself.
- Outputs are legal information and drafting/research support unless reviewed and adopted by a qualified human within an authorized framework.
- Qualified humans retain responsibility for legal advice, professional judgment, filing, service, signing, disclosure, settlement, negotiation, and representation.

### 5.2 Required gates

Every external or court-ready output must pass applicable gates:

1. Matter access gate.
2. Consent / processing-basis gate.
3. Privilege and confidentiality gate.
4. Evidence support gate.
5. Citation verification gate.
6. Procedure and deadline gate.
7. Competency / supervising-reviewer gate.
8. Human approval gate.
9. Export audit gate.

### 5.3 Security requirements

V1 target security:

- MFA for production users.
- Session management and device controls.
- RBAC/ABAC with matter-level authorization.
- Ethical walls.
- TLS in transit.
- Encryption at rest.
- Per-matter key strategy where feasible.
- Append-only audit ledger with hash chaining.
- Secure object storage.
- Backups and restore testing.
- Rate limiting.
- Secrets management.
- Security event logging.
- Data retention and deletion/destruction workflows subject to legal holds.

### 5.4 Privacy and data governance

The platform must support:

- Consent records by purpose/category/model destination.
- Consent withdrawal handling.
- External model restrictions.
- Privacy notices and notice-version tracking.
- Data export and retention policies.
- Public-demo synthetic-data restrictions.
- Vendor/model review.
- Privacy impact assessment before real-client production.

## 6. Functional requirements

### 6.1 Identity and matter foundation

- Register organization.
- Invite users.
- Authenticate users.
- Enforce MFA in production.
- Create matters.
- Assign users to matters.
- Define roles and permissions.
- Perform conflict checks before matter activation.
- Record all access and changes in audit ledger.

### 6.2 Conversation and memory

- Persist conversations.
- Associate conversations with matter, mode, user, and selected sources.
- Support search across authorized chats.
- Keep general chats separate from matter chats.
- Store assistant reasoning outputs as reviewable artifacts where appropriate.
- Allow user to pin important responses into matter notes or tasks.

### 6.3 Document ingestion

- Upload documents to quarantine.
- Validate file type and size.
- Hash originals.
- Extract native text where available.
- OCR scanned pages.
- Page-index extracted text.
- Classify document type.
- Detect duplicates and versions.
- Extract metadata.
- Run privilege and sensitivity screening.
- Require human review for low-confidence results.

### 6.4 Evidence matrix

- Create evidence nodes from document spans.
- Classify each proposition as fact, allegation, admission, inference, assumption, issue, law, or argument.
- Link proposition to source location.
- Track supporting and contradicting evidence.
- Track confidence and human review status.
- Surface gaps and contradictions.

### 6.5 Legal research

- Search legal sources by query, citation, topic, jurisdiction, and date.
- Retrieve official statutes and regulations.
- Retrieve court/tribunal authorities from approved sources.
- Verify citation and pinpoint.
- Analyze case treatment and binding weight.
- Lock legal-source snapshots for outputs.

### 6.6 Drafting and exports

- Generate draft artifacts from templates and matter context.
- Highlight unsupported facts and unverified law.
- Provide revision instructions and redlines.
- Maintain version history.
- Export approved outputs to DOCX/PDF/PDF-A/ZIP.
- Include manifests showing evidence, authority, privilege, procedure, and approval states.

### 6.7 Tasks and collaboration

- Create tasks manually and from chat/document events.
- Assign tasks to users.
- Set due dates and priorities.
- Link tasks to documents, evidence, citations, drafts, and conversations.
- Comment on documents and artifacts.
- Maintain notification feed.

### 6.8 Automation agents

- Agents must create an explicit plan.
- User can approve, edit, or cancel the plan.
- Each agent step must be auditable.
- External actions require separate approval.
- Agents must stop on critical legal, privilege, citation, consent, or access failures.

## 7. Technical architecture

### 7.1 Architecture style

V1 uses a **modular monolith** with isolated background workers.

```text
FastAPI modular monolith
├── identity
├── matters
├── consent
├── conflicts
├── privilege
├── ingestion
├── evidence
├── knowledge
├── citations
├── reasoning
├── drafting
├── deadlines
├── tasks
├── collaboration
├── export
├── notifications
└── audit

Workers
├── OCR
├── transcription
├── embeddings
├── knowledge updates
├── citation treatment refresh
├── document rendering
├── evaluation jobs
└── notification delivery
```

Split into independent services only when scale, security isolation, release cadence, or stable API boundaries justify it.

### 7.2 Data stack

| Component | Use |
|---|---|
| PostgreSQL | Users, orgs, matters, permissions, conversations, evidence, citations, tasks, approvals, audit metadata |
| pgvector | Matter and legal-source embeddings |
| S3-compatible object storage | Originals, extracted pages, media, exports, rendered artifacts |
| Redis | Queues, short-lived cache, locks, rate limits |
| Optional later: Neo4j | Only if relationship complexity exceeds relational graph tables |

### 7.3 Core data objects

Required objects:

- Organization
- User
- Role
- Matter
- Party
- ConflictCheck
- ConsentRecord
- Conversation
- Message
- Document
- DocumentPage
- DocumentSpan
- EvidenceNode
- EvidenceRelationship
- LegalSource
- Authority
- CitationVerification
- LegalTest
- DraftArtifact
- DraftVersion
- Annotation
- Task
- Approval
- ExportManifest
- AuditEvent
- RetentionPolicy
- LegalHold

### 7.4 AI orchestration

The AI layer must use retrieval-first, tool-aware orchestration:

1. Classify request and mode.
2. Check authorization and matter scope.
3. Check consent and model-destination policy.
4. Retrieve approved matter sources and/or legal sources.
5. Run citation/evidence/procedure checks as needed.
6. Generate answer/draft/plan with source links.
7. Mark unsupported or unverified material.
8. Route to human approval when needed.
9. Log audit events.

### 7.5 Model strategy

- RAG-first for legal truth.
- Private/local model support where feasible.
- External model use only where consent and policy allow it.
- Model outputs are never authoritative without source verification.
- Fine-tuning is deferred until the retrieval, citation, and evaluation systems are mature.

### 7.6 API requirements

Representative API groups:

- `/v1/platform/auth/*`
- `/v1/platform/orgs/*`
- `/v1/platform/matters/*`
- `/v1/platform/conversations/*`
- `/v1/platform/documents/*`
- `/v1/platform/evidence/*`
- `/v1/platform/research/*`
- `/v1/platform/citations/*`
- `/v1/platform/drafts/*`
- `/v1/platform/tasks/*`
- `/v1/platform/approvals/*`
- `/v1/platform/exports/*`
- `/v1/platform/settings/*`
- `/v1/platform/audit/*`

Every endpoint that touches matter data must enforce authenticated actor, org scope, matter permission, audit logging, and public-demo restrictions.

### 7.7 Frontend architecture

Use the existing React/Vite platform UI as the shared frontend:

- Web application.
- Installable PWA.
- Tauri desktop shell.
- Tauri mobile shells where appropriate.

Core frontend modules:

- Workspace shell.
- Conversation panel.
- Work panel.
- Document editor.
- Source/citation viewer.
- Evidence matrix viewer.
- Task board.
- Approval queue.
- Settings center.
- Admin/security console.
- Client portal views.

### 7.8 Accessibility and localization

V1 targets:

- WCAG 2.1 AA-aligned UI practices.
- Keyboard navigation.
- Screen-reader labels.
- Adjustable text size and contrast.
- Plain-language summaries.
- Configurable output language.
- Initial multilingual support roadmap: English first; French, Punjabi, Mandarin, and Tagalog as target languages.

## 8. Product safety rules

Non-negotiable rules:

1. No public client intake before matter isolation.
2. No legal conclusion before verified authority.
3. No model fine-tuning before RAG evaluation.
4. No court-ready output before procedural validation.
5. No disclosure before privilege review.
6. No definitive deadline before human confirmation.
7. No real matter data in public Git or public Hugging Face Spaces.
8. No production release before legal and security evaluation.
9. No feature ships by demo alone when dependencies are unfinished.
10. No personalization setting may disable legal safety gates.

## 9. Success metrics

| Metric | Target |
|---|---:|
| Cross-matter leakage | 0 |
| Unverified citations in court-ready output | 0 |
| Unsupported facts in finalized output | 0 |
| Privilege-gate bypasses | 0 |
| Deadline benchmark accuracy | 100% on approved critical fixtures |
| Page-level provenance coverage | 100% for finalized factual propositions |
| Legal golden-set pass rate | ≥95% overall; 100% on critical controls |
| Critical security findings at release | 0 |
| Human approval coverage for external outputs | 100% |
| Public demo confidential-data findings | 0 |
| Backup restore success | 100% in scheduled tests |

## 10. MVP definition

The first credible MVP is not a full studio. It is a **secure, synthetic-data internal alpha** that demonstrates the core operating model:

- Authenticated users.
- Matter-scoped conversations.
- Basic settings profile.
- Document upload quarantine for text/PDF.
- Page-indexed extraction for supported files.
- Evidence node creation with source links.
- Research/citation verification scaffold connected to approved source registry.
- Draft artifact editor with unsupported-fact and unverified-citation warnings.
- Task creation from chat/draft/document events.
- Approval gate and audit manifest for exports.
- No real-client production claims.

## 11. Open decisions

1. Which deployment model ships first: local-only, private cloud, or firm-hosted cloud?
2. Which jurisdictions beyond BC are in scope for early domain settings?
3. Which external models, if any, are permitted under consent policy?
4. What is the exact encryption model: true E2EE for messaging-only, AI-enabled workspace encryption, or both in separate modes?
5. Which document editor component should be adopted for redlines/versioning?
6. Which OCR engine should be primary for production: local, cloud, or hybrid?
7. Which legal-source providers are approved for case-law retrieval and treatment beyond official statute sources?
8. What Law Society / regulatory authorization path governs real-client pilots?

## 12. Immediate engineering notes

Observed issues to fix early:

- Add missing `import re` in `backend/api/platform_routes.py` if not already present elsewhere.
- Correct `verifyCitation` in `apps/platform-ui/src/lib/api.ts` to send `citation_text`, `matter_id`, and `expected_topic` instead of undefined `content`.
- Keep `/workspace/analyze` unauthenticated only for synthetic/public-safe triage; real matter analysis must require authentication and matter ACL.
- Replace demo matter data with authenticated matter data when M1 UI integration is prioritized.

## 13. Release posture

This PRD/spec is aspirational for the studio target. Public communication must continue to distinguish:

- Implemented functionality.
- Internal alpha scaffolds.
- Roadmap targets.
- Features that require legal/security approval before use with real client data.

The product’s competitive advantage is not simply that it chats or drafts. It is that it turns AI assistance into a legally supervised, source-grounded, matter-isolated, auditable workflow.
