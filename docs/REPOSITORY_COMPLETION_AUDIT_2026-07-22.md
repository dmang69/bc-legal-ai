# Repository Completion Audit — Supreme Court Civil Litigation Counsel

**Assessment date:** 2026-07-22  
**Scope:** repository audit, counsel/BC tenancy skill integrity, and Hugging Face deployment  
**Target:** a supervised BC superior-court litigation workbench, not an autonomous lawyer

## Executive conclusion

The repository is a substantial prototype/internal-alpha foundation, but it is not ready for real-client production use or unsupervised legal work. The strongest implemented areas are structured legal reasoning schemas, evidence concepts, safety-oriented HITL components, counsel/tenancy skill packs, and a deterministic public demo. The principal completion gaps remain production identity and isolation, OCR and record provenance, official-source legal retrieval and authority treatment, deterministic deadline/procedure engines, court-ready export, privilege/security hardening, and legal evaluation.

A legal system is never permanently “complete”; the appropriate target is a **Production Candidate** that satisfies the M1–M8 release gates in `docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md`.

## What is actually present

| Area | Repository evidence | Assessment |
|---|---|---|
| Counsel and tenancy skills | `skills/supreme-court-civil-counsel/`, `skills/bc-tenancy-*` | Substantial, but contained stale and overbroad RTA propositions requiring correction and automated integrity checks |
| HITL controls | `services/reasoning/hitl/consent`, `exceptions`, `privilege_check`, `competency_gate` | Implemented prototype components; not proof of production persistence, authenticated review, or immutable operations |
| Knowledge base | `knowledgebase/primary_sources.py`, updater, citation verifier, treatment analyzer, snapshots | Scaffold/prototype; live official ingestion and treatment remain incomplete |
| Client/post-resolution layers | `frontend/client/`, `services/client_portal`, `messaging`, `post_resolution`, `retention` | Broad scaffolding; cryptography, MFA, persistent authorization, legal clocks, and production workflows remain incomplete |
| Platform core | FastAPI/backend modules, SQLite/Postgres-ready structures, React/Tauri scaffolds | Internal-alpha foundation; production multi-tenant operations and signed distribution not complete |
| Public Hugging Face Space | `huggingface-space/` | Deterministic public demo is the safe default; optional model loader required repair |
| Model strategy | `model/BASE_MODEL_DECISION.md` | Correct RAG-first Qwen2.5 posture; no bespoke trained “BC legal AI” checkpoint is established |
| Automated tests | `tests/` | Useful prototype coverage; not yet a legal golden-set, red-team, penetration, or release-certification suite |

## Priority completion backlog

### P0 — Release blockers and legal-integrity controls

1. **Finish public-history and repository remediation.** Complete history review/rewrite where required, rotate exposed credentials, protect `main`, and independently verify GitHub releases, Actions artifacts, issues, and Hugging Face repositories contain no live matter material.
2. **Eliminate stale legal propositions.** All skills, templates, UI copy, and tests must use the official RTA topic map (for example s. 5 contracting out, s. 28 quiet enjoyment, s. 29 entry). Block publication when prohibited legacy mappings recur.
3. **Make source verification enforceable.** A warning label is insufficient. Court-ready modes must reject unverified statutes, cases, forms, deadlines, policy guidelines, and treatment status.
4. **Remove false production claims.** Scaffolded MFA, encryption, E2E messaging, authority treatment, OCR, legal clocks, and exports must not be represented as operational.
5. **Repair Hugging Face model identity.** A policy/model card must never be presented as a Transformers architecture. Public deployment must default to no inference; private inference must use a standard reviewed model repository without `trust_remote_code=True`.

### P1 — Secure matter foundation (M1)

1. Production authentication with MFA/recovery/session/device controls and rate limiting.
2. Organization, user, client, party, matter, assignment, and role persistence in PostgreSQL.
3. Deny-by-default RBAC/ABAC, document ACLs, ethical walls, grant expiry, and revocation.
4. Conflict checks across aliases, former clients, opposing parties, addresses, and organizations.
5. Granular consent, withdrawal propagation, derived-data handling, and versioned notices.
6. Append-only, tamper-evident audit storage with actor identity and export/access/approval events.
7. Encrypted object storage, backups, migration discipline, and tested restore procedures.

**Exit evidence required:** authenticated actor on every operation; adversarial cross-matter isolation tests; conflict and consent gates; verified audit chain; successful backup restore.

### P1 — Production ingestion and evidence provenance (M2)

1. Quarantine and malware/type validation before parsing.
2. Native extraction plus OCR for scanned PDFs and images, with page coordinates and confidence.
3. Audio/video transcription with timestamps and speaker review; replace transcription stubs.
4. Immutable originals, cryptographic hashes, chain of custody, derived-layer versioning, and duplicate detection.
5. Persistent Evidence Matrix with page/span provenance, contradiction links, human review state, and concurrency safety.
6. Chunked/page-indexed processing that does not truncate a complete record to one model context.

**Exit evidence required:** every proposition traces to an immutable source location; low confidence routes to review; state survives restart/concurrency.

### P1 — Official legal knowledge and citation verification (M3)

1. Automated BC Laws ingestion with currency lines, effective dates, regulations, legislative-change monitoring, and point-in-time snapshots.
2. RTB Rules, forms, policy guidelines, and decisions with version/effective-date metadata.
3. BCSC/BCCA/SCC authority ingestion with court hierarchy, precedential weight, pinpoints, appellate history, and treatment.
4. Hybrid lexical/vector retrieval with matter/public-source separation and provenance.
5. Citation verification that checks existence, pinpoint support, jurisdiction, currency, and treatment—not merely citation shape.
6. Change alerts that invalidate or flag affected legal tests, templates, and active matter analyses.

**Exit evidence required:** superseded sources cannot enter court-ready output; central propositions have verified primary support and pinpoints.

### P1 — Controlled reasoning and human review (M4)

1. Lawyer-approved, versioned LegalTest registry tied to effective law and jurisdiction.
2. Structured issue/rule/evidence/application/counterargument/remedy outputs with FACT/ALLEGATION/LAW/ARGUMENT/INFERENCE/ASSUMPTION separation.
3. Private, pinned inference configuration with cost/token/rate controls and no public-client data path.
4. Critical exceptions that freeze output and route to a qualified supervisor.
5. Authenticated privilege review and two-person approval where policy requires it.
6. Competency, licensing/currency, conflict, and backup-reviewer gates.
7. Mandatory both-sides analysis and explicit evidentiary gaps.

### P1 — Procedure, deadlines, drafting, and export (M5)

1. Deterministic deadline engine keyed to event, service method, deemed receipt, weekends/holidays, extension authority, and human confirmation.
2. Versioned BCSC Civil Rules, practice directions, registry requirements, filing fees, and RTB Rules/forms.
3. Validated form generation for petitions, responses, applications, affidavits, orders, RTB materials, and service documents.
4. Record-linked drafting: every fact maps to evidence; every legal proposition maps to verified authority.
5. Books of authorities/documents with indexes, bookmarks, tabs, redaction, and citation cross-references.
6. Court-quality DOCX, searchable PDF/PDF-A, and package ZIP rendering with visual regression checks.
7. Privilege, privacy, procedural, and human approval gates before export.

### P2 — Client delivery and local connector (M6)

1. Complete portal authentication, matter dashboard, evidence review, messaging, consent, tasks/deadlines, and decision/enforcement views.
2. Implement accurately described cryptography; remove placeholder E2E claims until independently reviewed.
3. Accessibility testing to WCAG target, screen-reader and keyboard support, mobile layouts, and reviewed translations.
4. Approved-folder-only Windows connector with preview, exclusions, consent, privilege classification, deduplication, revocation, and local audit.
5. Signed Tauri installers and controlled PWA/store distribution after backend gates pass.

### P2 — Post-resolution operations (M7)

1. Human-confirmed order/obligation extraction and outcome tracking.
2. Compliance monitoring and enforcement workflows tailored to order and court type.
3. JR trigger analysis and deadline calculation from verified legislation/rules; remove placeholder universal “60-day” assumptions.
4. Stay workflow with record-linked affidavits and verified authorities.
5. Retention schedules approved for the operating legal context, legal holds, client requests, and destruction of originals/derivatives/indexes/backups according to policy.

### P2 — Production hardening and controlled pilot (M8)

1. Lawyer-approved golden matters covering tenancy, RTB JR, civil applications, evidence, remedies, and adverse authorities.
2. Citation hallucination, stale-law, wrong-jurisdiction, deadline, and procedural-form benchmarks.
3. Privilege and prompt-injection red teams; cross-matter leakage and authorization abuse tests.
4. Threat model, penetration test, dependency/SBOM scanning, incident-response exercise, and disaster recovery test.
5. Privacy impact assessment, vendor/model/data-residency review, accessibility audit, and supervising-user training.
6. Narrow pilot charter, client disclosures, rollback criteria, incident ownership, and formal release approval.

## Counsel and tenancy skill-specific gaps

1. Replace stale internal references to s. 6 as “cannot contract out” with s. 5.
2. Replace stale quiet-enjoyment references to s. 22 with s. 28 and entry references to ss. 25–26 with s. 29.
3. Remove the proposition that RTA s. 8 limits charges; official s. 8 concerns appointment of the director. Analyze fees through the actual tenancy agreement, RTA/regulation provisions, standard terms, deposits, services/facilities, damages, and applicable strata/bylaw law.
4. Do not describe s. 47.1 as a general retaliation prohibition; official s. 47.1 is within landlord notice-for-cause provisions and must be applied from its current text.
5. Distinguish s. 51.2 right of first refusal from s. 51.3 compensation for no right of first refusal.
6. Treat policy guidelines as non-binding guidance and verify titles/current versions.
7. Remove categorical evidence hierarchies, guaranteed outcomes, fixed abatement percentages, and “no exceptions” deadline language unless supported and qualified.
8. Distinguish RTB informal evidence rules (RTA s. 75) from court evidence and affidavit rules.
9. Require official-source verification timestamps and a jurisdiction/effective-date block before court drafting.
10. Add automated forbidden-claim scans as a publication gate.

## Hugging Face release architecture

### Public Space

- Deterministic, synthetic-only demonstration.
- No uploads, persistence, connectors, confidential data, court-ready exports, or default model inference.
- Gradio metadata and runtime must agree; if static deployment is desired, use a distinct static Space configuration rather than contradictory documentation.

### Public dataset

- Curated public skills, templates, checklists, and verified extracts only.
- Exclude matters, evidence, transcripts, recordings, credentials, caches, generated archives, and unsupported binaries.
- Generate a checksum manifest and auditable skipped-file report before upload.

### Model repository

- Either publish a genuine standard checkpoint/adapter with valid config, tokenizer, weights, licence, base-model attribution, evaluation, and model card, or label the repository documentation-only and never pass it to Transformers.
- For the selected deployable base, load `Qwen/Qwen2.5-7B-Instruct` or a complete standard-compatible derivative with `AutoTokenizer` and `AutoModelForCausalLM` and without remote code.
- Copying base-model files to a new repository does not create a legally specialized model and must preserve licence/attribution and model identity.

## Release recommendation

**Current recommended classification:** **Prototype / Internal Alpha foundation**.  
**Permitted use:** synthetic demonstrations, engineering development, and supervised experimentation with approved non-confidential material.  
**Not permitted yet:** public real-client intake, claims of legal advice or representation, unsupervised deadline reliance, court-ready filing without human verification, or production handling of privileged matter records.

The next release gate should be **M1 secure foundation + M2 provenance**, not model fine-tuning or autonomous agents. M3 verified law and M5 procedure/export must pass before any “court-ready” claim.
