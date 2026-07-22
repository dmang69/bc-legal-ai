# Phase 3 — API and Database Contract

**Project:** BC Legal AI Associate (`dmang69/bc-legal-ai`)  
**Artifact type:** Engineering contract (schemas + endpoints)  
**Status:** v0.1 — implement against this before portal/production wiring  
**Not legal advice.** Confirm BC Laws / SCR / ATA / PIPA text before reliance.

---

## 0. Six design locks (non-negotiable)

| # | Rule | Contract implication |
|---|------|----------------------|
| 1 | **Consent ≠ privilege** | `consents` never writes `privilege_class` or `waiver`. Privilege lives in privilege tables only. |
| 2 | **Withdrawal ≠ unconditional deletion** | Withdrawal blocks *optional* AI; PIPA reasonable notice; `legal_hold` / `processing_basis` may retain; separate disposition workflow. |
| 3 | **Form 66 starts petition; Form 67 is response** | Templates: `form_number` 66=PETITION, 67=RESPONSE_TO_PETITION; stay/application → Form 32 / 33; affidavit → Form 109. |
| 4 | **JR clock: 60 days from final decision issuance** | Default calc uses issuance date; alternatives when finality/issuance/enabling Act uncertain; ATA s.57(2) extension is a *human* pathway, not auto-granted. |
| 5 | **No dual claim E2EE + server AI** | `messaging.encryption_model` is either `MODEL_A_E2EE` or `MODEL_B_WORKSPACE` — never both AI-on-server and inaccessible-to-server. |
| 6 | **RTB archive incomplete** | `rtb_decision.archive_completeness = PARTIAL`; absence ≠ non-existence. |

**Dependencies before Phase 4 real client data:** Layer 0–2, audit, auth/matter isolation, UPL compliance, eval suite.

---

## 1. Identity and tenancy conventions

| Field | Type | Notes |
|-------|------|--------|
| `id` | `text` PK | Prefixed ULID-style: `consent_…`, `exc_…`, `appr_…`, `ksrc_…` |
| `matter_id` | `text` NOT NULL | Matter partition; all queries filter by matter ACL |
| `created_at` / `updated_at` | `timestamptz` | UTC |
| Append-only audit | separate tables | Never UPDATE audit rows |

Postgres is system of record for contracts and relationship tables (V1). Object store holds blobs by id. Neo4j is deferred until relational graphs prove insufficient (see `architecture/MODULAR_MONOLITH.md`).

---

## 2. Consent

### 2.1 Tables

**`consents`**

| Column | Type | Constraints |
|--------|------|-------------|
| `consent_id` | text | PK |
| `matter_id` | text | NOT NULL, FK matters |
| `subject_id` | text | NOT NULL (client principal) |
| `category` | text | enum consent_category |
| `purpose` | text | NOT NULL, purpose-specific |
| `processing_scope` | jsonb | array of operations |
| `model_scope` | text | `NONE` \| `PRIVATE_INFERENCE_ONLY` \| `EXTERNAL_MODEL` |
| `status` | text | state machine |
| `notice_version` | text | NOT NULL |
| `granted_at` | timestamptz | nullable |
| `expires_at` | timestamptz | nullable |
| `withdrawn_at` | timestamptz | nullable |
| `captured_by` | text | e.g. client_portal |
| `authentication_event` | text | nullable |
| `signature_hash` | text | nullable |
| `plain_language` | text | versioned explanation snapshot |
| **Forbidden columns** | — | No `privilege_*`, no `waiver_*` |

**`consent_audit_events`** (append-only)

| Column | Type |
|--------|------|
| `entry_id` | text PK |
| `ts` | timestamptz |
| `matter_id` | text |
| `subject_id` | text |
| `action` | text (`GRANT`, `WITHDRAW`, `DENY_GATE`, `PRIVILEGE_UNCHANGED`, …) |
| `category` | text |
| `consent_id` | text nullable |
| `detail` | text |

**`consent_derived_artifacts`**

| Column | Type |
|--------|------|
| `consent_id` | text |
| `artifact_id` | text |
| `artifact_kind` | text (`embedding`, `summary`, `graph_node`, …) |

**`matter_processing_blocks`**

| Column | Type |
|--------|------|
| `matter_id` | text PK |
| `optional_ai_blocked` | boolean |
| `reason` | text |
| `effective_at` | timestamptz |

### 2.2 State machine

```text
DRAFT → PRESENTED → GRANTED → ACTIVE → MODIFIED
  → WITHDRAWAL_REQUESTED → RESTRICTED → WITHDRAWN | EXPIRED
Alt: DECLINED | LEGAL_BASIS_REVIEW | PROCESSING_PERMITTED_WITHOUT_CONSENT
```

### 2.3 Withdrawal semantics (PIPA-aligned design)

On `POST /consents/{id}/withdraw`:

1. **Immediate:** set `optional_ai_blocked` for affected categories; cancel queued *optional* jobs; invalidate capability tokens; remove from ordinary AI search index.
2. **Not automatic:** physical delete of originals under legal hold / litigation / statutory retention.
3. **Assess:** legal hold, retention class, whether another **processing basis** exists (legal obligation / permitted without consent → `LEGAL_BASIS_REVIEW`).
4. **Client notice:** consequences in plain language; reasonable notice for remaining disposition steps.
5. **Audit:** immutable `WITHDRAW` + explicit `PRIVILEGE_UNCHANGED`.

### 2.4 HTTP API

```http
POST   /v1/matters/{matter_id}/consents
GET    /v1/matters/{matter_id}/consents
PATCH  /v1/consents/{consent_id}
POST   /v1/consents/{consent_id}/withdraw
GET    /v1/consents/{consent_id}/history
POST   /v1/consents/evaluate-operation
```

**`POST /v1/consents/evaluate-operation` body**

```json
{
  "matter_id": "matter_…",
  "subject_id": "client_…",
  "data_categories": ["MEDICAL_INFORMATION"],
  "purpose": "extract_dates",
  "model_destination": "PRIVATE_INFERENCE_ONLY"
}
```

**Response**

```json
{
  "permitted": false,
  "basis": "NONE",
  "reasons": ["Missing consent categories: MEDICAL_INFORMATION"],
  "required_consents": ["MEDICAL_INFORMATION"],
  "privilege_review_required": false,
  "freeze_export": false
}
```

`basis` values: `CONSENT` | `LEGAL_OBLIGATION` | `LEGITIMATE_INTEREST_REVIEW` | `PROCESSING_PERMITTED_WITHOUT_CONSENT` | `NONE`.

---

## 3. Exceptions

### 3.1 Table `exceptions`

| Column | Type | Notes |
|--------|------|-------|
| `exception_id` | text PK | |
| `matter_id` | text | |
| `task_id` | text nullable | |
| `category` | text | taxonomy enum |
| `severity` | text | INFO\|NOTICE\|WARNING\|HIGH\|CRITICAL |
| `summary` | text | no raw client content |
| `affected_artifacts` | jsonb | ids only |
| `raw_client_content_logged` | boolean | **always false** (check constraint) |
| `detected_by` | text | |
| `model_id` | text nullable | |
| `prompt_template_version` | text nullable | |
| `status` | text | OPEN\|ASSIGNED\|RESOLVED |
| `assigned_reviewer` | text nullable | |
| `resolution` | text nullable | human reason required for RESOLVED |
| `resolution_by` | text nullable | must not be `ai`/`system` for CRITICAL |
| `freeze_export` | boolean | |
| `block_workflow` | boolean | |
| `proposed_content_quarantined` | boolean | |
| `created_at` | timestamptz | |

### 3.2 API

```http
POST /v1/matters/{matter_id}/exceptions
GET  /v1/matters/{matter_id}/exceptions?status=OPEN
POST /v1/exceptions/{exception_id}/assign
POST /v1/exceptions/{exception_id}/resolve
GET  /v1/matters/{matter_id}/export-freeze
```

CRITICAL: auto-set matter freeze; resolve requires human id + non-empty reason.

---

## 4. Approvals and productions

### 4.1 Tables

**`production_packages`**

| Column | Type |
|--------|------|
| `production_id` | text PK |
| `matter_id` | text |
| `output_class` | text |
| `status` | text |
| `snapshot_hash` | text NOT NULL |
| `recipient` | text |
| `reviewer_id` | text nullable |
| `approver_id` | text nullable |
| `manifest_json` | jsonb nullable |
| `manifest_signature` | text nullable |

**`approval_records`** (append-only)

| Column | Type |
|--------|------|
| `approval_id` | text PK |
| `production_id` | text |
| `stage` | text REVIEW\|APPROVE |
| `actor_id` | text |
| `decision` | text |
| `snapshot_hash` | text |
| `notes` | text |
| `ts` | timestamptz |

High-risk `output_class` requires `reviewer_id ≠ approver_id` unless `same_person_override_reason` set.

### 4.2 API

```http
POST /v1/matters/{matter_id}/productions/freeze
POST /v1/productions/{production_id}/review
POST /v1/productions/{production_id}/approve
POST /v1/productions/{production_id}/release
GET  /v1/productions/{production_id}
```

Release fails if `hash(body+docs+derivatives) ≠ snapshot_hash`.

---

## 5. Knowledge source

### 5.1 Tables

**`knowledge_sources`**

| Column | Type |
|--------|------|
| `source_id` | text PK |
| `name` | text |
| `authority_type` | text OFFICIAL_PRIMARY\|SECONDARY |
| `jurisdiction` | text |
| `permitted_content` | jsonb |
| `retrieval_method` | text |
| `health_status` | text |
| `terms_reviewed_at` | timestamptz nullable |
| `last_successful_update` | timestamptz nullable |

**`statutory_provisions`** (BC Laws only for BC statute text)

| Column | Type |
|--------|------|
| `provision_id` | text PK |
| `source_id` | text FK → source_bc_laws |
| `act` | text |
| `section` | text |
| `text` | text |
| `effective_from` | date nullable |
| `effective_to` | date nullable |
| `source_version` | text |
| `source_hash` | text |
| `retrieval_date` | date |

**`rtb_decisions`**

| Column | Type | Notes |
|--------|------|-------|
| `decision_id` | text PK | |
| `citation_or_file` | text | |
| `publication_source` | text | e.g. official archive |
| `publication_category` | text | |
| `archive_coverage` | text | **PARTIAL** default |
| `anonymization_status` | text | |
| `precedential_weight` | text | NON_BINDING_TRIBUNAL |
| `completeness_warning` | text | fixed disclaimer |
| `official_url` | text nullable | |

`completeness_warning` must state: absence from the RTB decision archive is **not** proof that no decision exists.

**`analysis_snapshots`**

| Column | Type |
|--------|------|
| `knowledge_snapshot_id` | text PK |
| `matter_id` | text |
| `statutory_version_ids` | jsonb |
| `rules_version_ids` | jsonb |
| `template_version_ids` | jsonb |
| `authority_verification_time` | timestamptz |
| `analysis_ref` | text |
| `change_notices` | jsonb |

### 5.2 API

```http
GET  /v1/knowledge/sources
GET  /v1/knowledge/sources/{source_id}
POST /v1/knowledge/citations/verify
POST /v1/knowledge/snapshots
GET  /v1/knowledge/snapshots/{id}
GET  /v1/knowledge/templates?forum=BC_SUPREME_COURT
```

Court-ready citation verify rejects `NOT_FOUND` / `REJECTED`.

---

## 6. JR limitation clock (contract)

**Default rule (ordinary RTB JR):** 60 days from **issuance of the final decision** (subject to human confirmation of finality and enabling legislation).

**Engine must emit alternatives when uncertain:**

| Scenario | `clock_mode` | Behaviour |
|----------|--------------|-----------|
| Issuance date known, final | `STANDARD_60_FROM_ISSUANCE` | primary deadline |
| Finality uncertain | `FINALITY_UNCERTAIN` | range + HITL flag |
| Issuance date unknown | `ISSUANCE_UNKNOWN` | no definitive client deadline |
| Enabling Act unclear | `ENABLING_ACT_UNCERTAIN` | alternatives list |
| Extension sought | `ATA_S57_2_EXTENSION_PATH` | track application; **not** auto-extend |

Reference: *Administrative Tribunals Act* s.57 (extension criteria are for counsel; system only tracks pathway).

---

## 7. Messaging encryption claim (contract)

| `encryption_model` | Server can read plaintext for AI? | UI label |
|--------------------|-----------------------------------|----------|
| `MODEL_A_E2EE` | No (unless user expressly exports decrypted copy to AI workspace) | “End-to-end encrypted” |
| `MODEL_B_WORKSPACE` | Yes, within matter service under consent | “Encrypted in transit and at rest (workspace)” — **not** E2EE |

Check constraint: cannot set `e2e_claimed=true` and `server_side_ai_enabled=true`.

---

## 8. Artifact locations in repo

| Artifact | Path |
|----------|------|
| This contract | `architecture/contracts/PHASE_3_API_DB_CONTRACT.md` |
| SQL DDL | `architecture/contracts/sql/phase3_core.sql` |
| JSON Schema | `architecture/contracts/json_schema/*.json` |
| OpenAPI fragment | `architecture/contracts/openapi/phase3_hitl.yaml` |
| Python validators | `architecture/contracts/models.py` |
| Runtime HITL | `services/reasoning/hitl/` |
| JR clock | `services/deadlines/jr_clock.py` |

---

## 9. Implementation order (next)

1. Apply `phase3_core.sql` to Postgres (dev compose).  
2. Wire FastAPI routers to `HitlControlPlane` + contracts validators.  
3. Migration tests: consent cannot set privilege; withdraw cannot delete held rows.  
4. Only then: portal MFA + quarantine object store.
