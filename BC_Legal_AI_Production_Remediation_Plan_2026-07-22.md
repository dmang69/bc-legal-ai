# BC Legal AI — Production Remediation Plan

**Audit date:** 2026-07-22  
**Plan generated:** 2026-07-23  
**Current classification:** Internal Alpha / Prototype — NOT production-ready

---

## Executive Summary

This document translates the Production Readiness Audit findings into actionable workstreams, sequenced by urgency. Each workstream maps to specific files in the repository with concrete code changes required.

**Bottom line:** 8 of 17 audit findings have already been remediated. The remaining 9 findings require focused engineering work before this system can be considered production-ready.

### Already Fixed (8 findings)
| Finding | Remediation |
|---------|-------------|
| 2. Ethical wall bypass | Deny-first authorization in `can_access_matter()` |
| 3. Competing API security | All routes use `CurrentUser` dependency |
| 4. Citation/deadline auth | Matter access validated before operations |
| 9. CORS unrestricted | Environment-specific allowlist with startup guard |
| 10. Health check truthfulness | `/health/live` + `/health/ready` with dependency checks |
| 11. CI/Docker consistency | Single dependency graph via `pyproject.toml` extras |
| 14. Deadline spoofing | `human_confirmed` forced `False` from API |
| 16. Drafting error hiding | Narrow exception handling; explicit degraded/error states |

### Still Broken (9 findings)
| Finding | Priority | Effort |
|---------|----------|--------|
| 1. PostgreSQL support | **P0** | 3 days |
| 5. Evidence quarantine | **P0** | 5 days |
| 6. HITL state persistence | **P0** | 10 days |
| 7. Audit chain concurrency | **P0** | 3 days |
| 8. Browser session tokens | **P0** | 5 days |
| 12. Redis/MinIO integration | **P0** | 5 days |
| 13. Job queue double-execution | **P0** | 3 days |
| 15. Citation verification | **P0** | 8 days |
| 17. HuggingFace model | **P0** | 1 day |

---

## Release Gates

### Gate 0: Secure Foundation (P0 Complete)
All 9 broken findings must pass acceptance criteria. Required before any:
- Real client data processing
- Multi-tenant deployment
- Public beta

### Gate 1: Verified Legal Knowledge (P1)
- SQLAlchemy/Alembic persistence
- PostgreSQL RLS
- Evidence quarantine with real malware scanning
- BC Laws automated ingestion
- Citation verification with pinpoint support

### Gate 2: Controlled Supervised Product (P2)
- Persisted HITL workflows
- Deadline engine with holiday/weekend rules
- Court-ready document generation
- Privilege review gate

### Gate 3: Release Hardening (P3)
- Cross-matter adversarial tests
- Penetration testing
- Load/soak/chaos testing
- Accessibility audit
- Privacy impact assessment

---

## Workstream Details

See `P0_ENGINEERING_BACKLOG.md` for ticket-by-ticket tasks.

---

## 30/60/90-Day Plan

### Days 1-30: P0 Secure Foundation

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1-2 | PostgreSQL compat + Audit chain + Job queue | All 5 service files pass dual-backend tests |
| 1-2 | Session security (backend) | HttpOnly cookies, CSRF tokens, CSP headers |
| 3-4 | Evidence quarantine state machine | 7-state quarantine with magic-byte detection |
| 3-4 | HITL persistence (phase 1) | DB-backed consent + exception storage |
| 4 | Integration tests | Concurrent audit + job queue tests pass |

### Days 31-60: P1 Secure Foundation (Continued)

| Week | Focus | Deliverable |
|------|-------|-------------|
| 5-6 | HITL persistence (phase 2) | Production packages + approvals survive restart |
| 5-6 | Redis/MinIO integration | Evidence in S3, jobs in Redis |
| 7-8 | HuggingFace model repair | Valid Qwen2 checkpoint or documented adapter |

### Days 61-90: P1 Verification + Hardening

| Week | Focus | Deliverable |
|------|-------|-------------|
| 9-10 | Citation verification (phase 1) | BC Laws API integration + pinpoint validation |
| 11-12 | Full integration test suite | All P0/P1 items verified under concurrency |
| 12 | Release gate review | Pass all M1 secure-foundation gates |

---

## Go/No-Go Criteria

### This system MUST NOT be called production-ready until:

- [ ] Zero known cross-matter leakage
- [ ] Every protected operation is authenticated and authorized
- [ ] PostgreSQL and RLS tests pass
- [ ] Ethical walls override privileged roles
- [ ] MFA and secure session controls pass
- [ ] Actual malware quarantine is operational (not extension-only)
- [ ] Originals are immutable and encrypted in object storage
- [ ] Relied-on facts have exact page/span provenance
- [ ] Current and historical law are versioned and source-linked
- [ ] Central citations and pinpoints are verified
- [ ] Deadline fixtures achieve approved accuracy
- [ ] No court-ready output bypasses citation, evidence, privilege, or human approval
- [ ] Workflow state survives restart and horizontal scaling
- [ ] Audit integrity survives concurrency
- [ ] Backup restoration succeeds
- [ ] Legal, security, accessibility, and operational release gates pass

---

## Current Recommendation

**Do not advance to feature expansion.** Complete the P0 secure foundation first. Every feature built on an insecure foundation compounds technical debt and increases security risk.

The proper next milestone is **M1 secure foundation completion** — not unrestricted feature expansion.

