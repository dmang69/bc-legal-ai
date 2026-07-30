# BC Legal AI Platform — Prompt Pack & Deliverables

Reusable prompts and first-draft outputs for marketing, architecture, and rollout.

## Prompts (source)

See conversation / internal pack:

1. **Executive marketing** — one-pager + hero  
2. **Technical specification** — architecture, APIs, security, ops  
3. **Implementation plan** — 6-month pilot phases  

## Generated deliverables (this folder)

| File | Content |
|------|---------|
| [01-executive-marketing.md](01-executive-marketing.md) | Hero, features, scenarios, CTA |
| [02-technical-specification.md](02-technical-specification.md) | Spec with Live vs Target |
| [03-implementation-plan.md](03-implementation-plan.md) | Phases 0–5, RACI, metrics |

## Constraints (always)

- Not legal advice · fail-closed court readiness  
- Privacy / private inference preferred for sensitive data  
- Accuracy, transparency, extensibility, enterprise security  
- Do not invent LMSYS Elo, unsupervised filing, or false E2EE+server AI claims  

## System-style instruction (short, all three goals)

```text
You are advising on BC Legal AI Associate: a supervised BC legal workbench
(FastAPI + React) with Puter AI base, OpenClaw agents, Kimi long-context,
Arena multi-model eval, Ollama local, org ACL/audit, fail-closed court_ready.
Not a lawyer. Prefer private inference for sensitive data. Distinguish Live
vs Target. Output structured markdown (headings, tables, checklists).
```

## Related product docs

- [../ENTERPRISE_AI_SUITE.md](../ENTERPRISE_AI_SUITE.md)  
- [../PRODUCTION_READINESS.md](../PRODUCTION_READINESS.md)  
- [../../README.md](../../README.md)  
