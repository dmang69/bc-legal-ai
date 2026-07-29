# Security review baseline — v1.0.0

**Classification:** Engineering baseline (not a third-party pen-test)  
**Date:** 2026-07-28

## Authentication & sessions

| Control | Implementation | Notes |
|---------|----------------|-------|
| Password hashing | Salted hash in `backend/identity/passwords.py` | Min length 10 |
| Session tokens | Opaque token; stored as hash | Bearer and/or HttpOnly cookie |
| CSRF | Double-submit for cookie auth | `X-CSRF-Token` |
| Logout | Server-side revoke + cookie clear | |
| Rate limits | Login/register sliding window | Env-tunable |
| Public demo | Registration/persistence blocked | `public_demo` mode |

**Hardening still recommended:** MFA, refresh rotation, lockout policy, remove bearer-from-localStorage in hardened SPA builds.

## Authorization

| Control | Status |
|---------|--------|
| Matter ACL | `can_access_matter` deny-first |
| Ethical wall | Blocks owner/admin |
| Org isolation | Cross-org 403 tests |
| Org AI settings | Owner/admin only for mutations |

## Secrets

| Control | Status |
|---------|--------|
| `.env` gitignored | Yes |
| `.env.example` no real secrets | Yes |
| Confidential scanner CI | Yes |
| Docker image non-root | `appuser` uid 10001 |

## Data exposure

| Risk | Mitigation |
|------|------------|
| Court-ready leakage | Export manifests + gates; public_demo rejects |
| Prompt injection | Safety patterns; no tool auto-file |
| External LLM egress | `ALA_ALLOW_EXTERNAL_LLM` gate + org allowlist |
| Web research | Off by default; host allowlist |

## Headers & transport

| Control | Status |
|---------|--------|
| CSP / X-Frame-Options / nosniff | `SecurityHeadersMiddleware` |
| HSTS | When host not localhost |
| TLS | Terminate at reverse proxy / cloud LB |

## Dependency scanning

| Tool | CI |
|------|-----|
| Bandit | Runs; artifact uploaded (non-blocking findings review) |
| Confidential patterns | Blocking on main test job |

## Pre-public checklist (org)

- [ ] Pen-test / bug bounty  
- [ ] Privacy impact assessment for real client data  
- [ ] Secret manager + rotation runbook  
- [ ] Backup/restore drill for Postgres  
- [ ] Incident response contact  
