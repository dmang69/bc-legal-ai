# BC Legal AI Associate — Phase 4 Master Engineering Program

**Repository:** `dmang69/bc-legal-ai`  
**Controlling rule:** No feature may bypass an unfinished dependency merely because a demonstration can be made to work.

| Estimate | Value |
|----------|------:|
| Current maturity | ~25% |
| After Phase 4 (supervised beta) | ~70–80% |
| After Phase 5 (controlled production) | production release |
| Remaining work (approx.) | 485–695 tasks |

## Milestones

| ID | Name | Outcome |
|----|------|---------|
| **M0** | Critical Remediation | Public-repo + legal-integrity risks removed |
| **M1** | Secure Platform Foundation | Auth, isolation, consent, conflicts, audit |
| **M2** | Document & Evidence Platform | OCR, provenance, matrix, chronology |
| **M3** | Legal Knowledge Platform | Official law, PIT, retrieval, citations |
| **M4** | Legal Reasoning Platform | Tests, AI, agents, HITL |
| **M5** | Procedure & Court Production | Deadlines, forms, DOCX/PDF, books |
| **M6** | Client & Desktop Interfaces | Portal, messaging, Windows connector |
| **M7** | Post-Resolution Platform | Decisions, enforcement, JR, retention |
| **M8** | Production Hardening | Security, legal eval, controlled release |

## Critical path

```text
M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8
```

Parallel (only after dependencies allow):

- M2 document processing **with** M3 public-law ingestion  
- M5 templates **with** M4 agent design  
- M6 UI prototypes **with** M5 backends  

**No real client material in M6 before M1 and M2 pass.**

## Hard product rules

- No public client intake before matter isolation  
- No legal conclusion before verified authority  
- No fine-tuning before RAG evaluation  
- No court-ready output before procedural validation  
- No disclosure before privilege review  
- No definitive deadline before human confirmation  
- No real matter data in public Git or public HF Space  
- No production release before legal + security evaluation  

## Labels

See `docs/github/LABELS.md`.

## Issue template

See `.github/ISSUE_TEMPLATE/engineering_task.md`.

## M0 status (working tree)

Tracked in `docs/M0_RELEASE_GATE.md`.

## Metrics (targets)

| Metric | Target |
|--------|--------|
| Cross-matter leakage | 0 |
| Unverified cites in court-ready output | 0 |
| Privilege-gate bypasses | 0 |
| Public confidential-data findings | 0 |
| Human approval for external outputs | 100% |
