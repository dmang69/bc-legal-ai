# Milestone M0 — Critical Remediation (release gate)

**Objective:** eliminate confidentiality, legal-integrity, deadline, packaging, and public-demo risks.

**Controlling program:** [`PHASE_4_MASTER_ENGINEERING_PROGRAM.md`](PHASE_4_MASTER_ENGINEERING_PROGRAM.md)

No further feature development should be treated as “released” until M0 passes. Priority Zero is a **hard stop** before feature expansion.

## Gate checklist

| # | Condition | Working tree (2026-07-21) |
|---|-----------|---------------------------|
| 1 | Live matter content removed from working tree | **Pass** (synthetic DEMO-*) |
| 2 | Git history sanitized | **Human action** if ever pushed live data |
| 3 | Synthetic examples installed | **Pass** |
| 4 | Confidential scanner operational | **Pass** `scripts/scan_confidential.py` |
| 5 | Pre-commit scanner operational | **Pass** `.pre-commit-config.yaml` |
| 6 | CI confidentiality gate | **Pass** `.github/workflows/` |
| 7 | Incorrect s.56 test disabled | **Pass** |
| 8 | Prior outputs invalidated | **Pass** `legal_knowledge/invalidated_tests.json` |
| 9 | Section-topic validator operational | **Pass** `architecture/section_topic.py` |
| 10 | Hard-coded live deadlines removed | **Pass** (synthetic + states) |
| 11 | Deadline confirmation state | **Pass** `services/deadlines/states.py` |
| 12 | Main branch protected | **Human** — GitHub settings |
| 13 | Python package reproducible | **Pass** — `pyproject.toml` (add `uv.lock` when `uv` available) |
| 14 | Docker build passes | **Pass** `Dockerfile` |
| 15 | CI passes | After push + Actions enabled |
| 16 | Public demo rejects confidential uploads | **Pass** guards in Space + `APP_MODE` |

## Human-only remaining

1. `git filter-repo` / BFG history purge if remote ever held live matter  
2. GitHub: Settings → Branches → protect `main`  
3. Collaborators re-clone after history rewrite  
4. Lawyer-approved replacement legal tests (M0-011 / M4)
