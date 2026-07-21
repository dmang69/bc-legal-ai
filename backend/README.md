# Backend

Target modules (not fully implemented):

| Path | Responsibility |
|------|----------------|
| `api/` | HTTP / Space API surface |
| `auth/` | Accounts, sessions, RBAC |
| `matters/` | Isolated matter workspaces |
| `documents/` | Ingest, OCR, hash, derived text layer |
| `retrieval/` | BC Laws, CanLII, courts, RTB policy |
| `citations/` | Citation Clerk + treatment checks |
| `deadlines/` | Rules-based calculator (not LLM dates) |
| `drafting/` | Structured drafts from templates |
| `exports/` | DOCX + searchable PDF + verification report |
| `audit/` | Immutable action log |
| `privilege/` | Privilege state machine, tagger, access control, production gate |

**Security rule:** no cross-matter ambient authority. Every request is scoped to a matter ID and principal.

**Privilege rule:** privilege belongs to the **client** (`privilege_owner`), not the firm or AI. See [`architecture/PRIVILEGE.md`](../architecture/PRIVILEGE.md).
