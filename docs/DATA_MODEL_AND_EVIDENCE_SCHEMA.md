# BC Legal AI Associate — Data Model & Evidence Schema

| Field | Value |
|-------|--------|
| Version | **1.0** |
| Date | 2026-07-22 |
| Database | **PostgreSQL 16+** with **pgvector** |
| Encryption | AES-256-GCM at rest; TLS 1.3 in transit |
| SQL source | [`architecture/contracts/sql/v1_data_model.sql`](../architecture/contracts/sql/v1_data_model.sql) |
| Status | **Controlling production schema** (target) |

**Relationship to current runtime:** Dev/tests may still use the simplified SQLite M1 schema (`backend/db/migrate.py`). Production and docker-compose Postgres should migrate toward **v1_data_model.sql**. Application code will be adapted incrementally; do not drop SQLite support until the dual-backend adapter is complete.

---

## 1. Design principles

| Principle | Meaning |
|-----------|---------|
| **Matter isolation** | Every record is scoped to a matter; cross-matter access denied via **RLS** |
| **Evidence provenance** | Every derived record links back to source document at **page/paragraph** level |
| **Privilege-aware** | Privilege screening at ingestion; privileged material segregated |
| **Audit-first** | Every write produces an **immutable** audit ledger entry |
| **Temporal accuracy** | Point-in-time law; legal refs carry effective-date ranges |
| **Consent-bound** | Consent gates AI processing, privilege release, and sharing |

---

## 2. Entity-relationship overview

```text
USERS & AUTH
  users ──< user_roles >── roles
  users ──< matter_participants >── matters
  users ──< consent_records
  users ──< sessions
  users ──< devices

MATTERS
  matters
  ├── matter_tags
  ├── matter_relationships
  └── matter_timeline_entries

  ├── evidence_documents
  │    ├── evidence_pages
  │    ├── evidence_ocr_results
  │    ├── evidence_extractions
  │    ├── evidence_classifications
  │    ├── evidence_embeddings (pgvector)
  │    ├── evidence_privilege_screenings
  │    └── evidence_chain_of_custody
  │
  ├── evidence_items (logical propositions)
  │    ├── evidence_item_links
  │    └── evidence_item_relationships
  │
  ├── matter_authorities (matter-scoped use of legal_authorities)
  ├── deadlines / deadline_calculations / deadline_confirmations
  ├── draft_documents / versions / approvals
  ├── communications
  ├── privilege_records / privilege_releases
  ├── consent_records / consent_audits
  ├── physical_file_records / locations / movements
  └── audit_entries (hash-chained)
```

---

## 3. Domain summary

### 3.1 Users & auth

- `users`, `roles`, `user_roles`
- `devices` (platform fingerprint, trust, revoke)
- `sessions` (token hash, device, terminate)

### 3.2 Matters

- `matters` — forum, type, status, key dates, demo flag
- `matter_participants` — role + access_level + privilege_access
- `matter_timeline_entries` — confirmed/unconfirmed events

### 3.3 Evidence documents (files)

- Ingestion pipeline states: quarantine → scanning → … → completed / failed / rejected  
- OCR status + confidence  
- Privilege flag at document level  
- Pages, extractions, classifications, embeddings (vector 1536), privilege screenings, chain of custody  

### 3.4 Evidence items (propositions)

- Types: fact, allegation, admission, assumption, inference, legal_argument, …  
- Dispute status: unverified → confirmed_by_human (never silent allegation→fact)  
- Links to document/page/quote with support_type  
- Inter-item relationships (supports, contradicts, …)

### 3.5 Legal authorities

- Global `legal_authorities` catalog + verification + effective dates + binding weight  
- Matter-scoped `matter_authority_uses` and verification results  

### 3.6 Deadlines, drafts, communications, privilege, consent, physical files

See SQL for full column definitions.

### 3.7 Audit

Append-only `audit_entries` with `prev_hash` / `entry_hash` chain.

---

## 4. Row-level security (target)

Application sets:

```sql
SET app.current_user_id = '<uuid>';
-- optional: SET app.current_org_id = '<uuid>';
```

RLS policies require membership in `matter_participants` with `active` and `access_level != 'no_access'`.  
Privilege-flagged documents require `privilege_access = true`.

*Note:* Full RLS policies are defined in the SQL file as a template; enable carefully after app sets session variables.

---

## 5. Encryption & storage

| Layer | Approach |
|-------|----------|
| Transit | TLS 1.3 |
| At rest (DB) | Transparent disk/volume encryption + optional pgcrypto for secrets |
| Object store | AES-256-GCM objects; keys in vault; `storage_key` is path not plaintext matter content |
| Tokens / MFA secrets | Store only hashes / app-level encrypted blobs |

---

## 6. Migration path from M1 SQLite

| Current (SQLite M1) | Target (v1 Postgres) |
|---------------------|----------------------|
| `users` text ids | `users` UUID |
| `matters` / `matter_members` | `matters` / `matter_participants` |
| `documents` / `document_pages` / `propositions` | `evidence_documents` / `evidence_pages` / `evidence_items` + links |
| `audit_ledger` | `audit_entries` |
| `consents` | `consent_records` |
| `legal_test_registry` | keep + link to `legal_authorities` |

---

## 7. Implementation notes

1. **Apply** `v1_data_model.sql` on a clean Postgres 16+ with `CREATE EXTENSION vector` and `citext`.  
2. **Do not** point public demos at production DB.  
3. Embeddings dimension (`1536`) must match the chosen embedding model; change with migration if model changes.  
4. Original bytes live in object storage; DB holds metadata and derived layers only.
