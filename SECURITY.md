# Security and confidential data

**Public name:** BC Legal AI Associate — research / drafting **support** only.  
**Not** a lawyer. **Not** for unredacted client files on public Hugging Face Spaces.

## Priority Zero (2026-07-21 audit)

1. **No live matter content** in the public repository (real file numbers, party names, evidence, planning dashboards).
2. **Synthetic demos only** under `templates/` (e.g. `DEMO-JR-0001`).
3. **Secrets** never in git; rotate any token pasted in chat.
4. **Git history:** if live data was ever pushed, scrubbing the working tree is not enough — rewrite or filter history and force-protect `main`.

## Scanner

```bash
python scripts/scan_confidential.py
```

Exit code 1 if patterns such as `KAM-S-S-*` or known party names appear outside the allowlist.

## Public Space

- CPU demo only; no model inference; no confidential uploads.
- Real-client work: private Space, firm infrastructure, or Canadian-region private deploy with MFA + ACL.

## Reporting

If you find confidential data in a public branch, stop using that clone for public demos, rotate secrets, and treat the matter as a privacy incident under firm policy.
