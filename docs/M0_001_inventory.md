# M0-001 Inventory — confidential repository content

**Date:** 2026-07-21  
**Scope:** working tree (history purge is separate human step)

## Disposition

| Path / pattern | Disposition |
|----------------|-------------|
| `templates/case/*` live KAM file | **Synthesize** → `DEMO-JR-0001` |
| `templates/examination/*` real names | **Synthesize** → Alex Manager |
| `templates/explainers/*` live JR link | **Synthesize** |
| `legal_knowledge/invalidated_tests.json` | **Document** s.56 invalidation |
| `matters/**` | **Local only** (gitignored) |
| Skill `outputs/*.pdf` | **Ignore** (gitignored) |
| HF tokens in chat | **Rotate** (out of band) |

## Scanner

```bash
python scripts/scan_confidential.py
```

## History

If remote ever contained live matter strings: run history rewrite (filter-repo/BFG), force-push with org approval, require re-clone. See `SECURITY.md`.
