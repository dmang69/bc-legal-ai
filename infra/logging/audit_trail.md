# Audit trail scaffolding

**Purpose:** Privilege-sensitive and matter-lifecycle operations must leave an immutable record.

## Destinations (dev → prod)

| Channel | Dev | Prod |
|---------|-----|------|
| Application audit | `architecture.audit_event` + in-memory / JSONL | PostgreSQL `audit_events` |
| Privilege ops | `services.compliance.privilege_ops_log` | Same table + restricted access |
| HITL exceptions | `services.reasoning.hitl.exceptions` | Postgres + paging/on-call |
| Metrics | Prometheus (optional compose profile) | Managed metrics |

## Minimum fields

- `event_id`, `ts` (UTC)
- `matter_id`, `actor` (type + id)
- `action`, `result` (allowed / blocked)
- `privilege_class` when relevant
- `correlation_id` for multi-service pipelines

## Rules

- Never log raw privileged document bodies or secrets.
- Prefer hashes + node_ids over full text.
- Retention per LSBC / firm policy; purge engine is Phase 4 post-resolution.
