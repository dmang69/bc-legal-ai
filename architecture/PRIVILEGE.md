# Solicitor–Client Privilege Architecture — ALA

**Product:** BC Legal AI Associate (ALA)  
**Internal nickname only:** “AI Lawyer”  
**Status:** Phase 1 contracts + enforceable gate logic (no production KMS yet)  
**Principle:** One privilege mistake can disqualify the entire product.

Core rule: **Privilege belongs to the client**, not the firm, not the AI.  
The firm is a **custodian**. The system enforces client ownership at the data layer.

---

## 1. Privilege domain model

### State machine

```
UNCLAIMED → CLAIMED → ASSERTED → UPHELD | WAIVED | PIERCED
```

| State | Meaning |
|-------|---------|
| UNCLAIMED | No privilege assertion recorded |
| CLAIMED | Privilege claimed; protected from casual export |
| ASSERTED | Asserted in a proceeding |
| UPHELD | Privilege upheld (e.g. after challenge) |
| WAIVED | Client-authorized waiver (logged) |
| PIERCED | Privilege found not to apply / pierced |

### Every privileged-capable record carries

| Field | Rule |
|-------|------|
| `privilege_status` | enum (state machine) |
| `privilege_basis` | solicitor_client \| litigation \| settlement_implied \| none |
| `privilege_owner` | **client_id** (never firm_id) |
| `claim_date` | timestamp when claimed |
| `asserted_in` | proceeding_id or None |
| `waiver_events` | append-only event log |

Implementation: `architecture/privilege_schemas.py`, transitions in `backend/privilege/state_machine.py`.

---

## 2. Communication classification pipeline

Every artifact (email, PDF, SMS, voice transcript, chat log) passes the **Privilege Tagger before storage**.

### Stage 1 — Context detection

- Who sent? → `sender_role`  
- Who received? → `recipient_role`  
- Legal advice sought/offered? → NLI / classifier (future fine-tune)  
- Litigation pending/contemplated? → cross-ref active proceedings  

### Stage 2 — Tag assignment (first-pass rule)

```
IF (sender in {client, lawyer}) AND (recipient in {lawyer, client})
   AND (advice_sought OR advice_given OR litigation_context)
THEN privilege_basis ∈ {solicitor_client, litigation}
ELSE privilege_basis = none
```

### Stage 3 — Human confirmation gate

- Confidence **&lt; 0.85** → **must** go to manual review  
- Tags are **never auto-finalized** without explicit confirmation  

**Why:** Misclassification is a top cause of **inadvertent waiver**. Privileged material tagged `none` and produced in discovery is catastrophic.

Spec for training data / annotation: `architecture/privilege_classifier_spec.md`.

---

## 3. Access control — zero-trust privilege boundary

### Roles

| Role | Access |
|------|--------|
| `client_principal` | Owns data; full read on own matters |
| `instructing_lawyer` | Full read/write on assigned matters |
| `associate_lawyer` | Read/write assigned; no delete |
| `paralegal` | Read on assigned tasks; write task artifacts |
| `ai_associate` | Read **only** on explicitly scoped matters/tasks |
| `opposing_counsel` | **NO ACCESS** (system-enforced) |
| `tribunal_court` | **NO DIRECT ACCESS** (production interface only) |

### AuthZ rule (query layer, not app-only)

```sql
SELECT * FROM documents
WHERE matter_id IN (
    SELECT matter_id FROM matter_access
    WHERE user_id = :current_user
      AND access_level >= :required_level
)
AND privilege_status IN (
  -- ai_associate: never WAIVED/PIERCED/UNCLAIMED bulk dump;
  -- only explicitly scoped CLAIMED/ASSERTED/UPHELD per task grant
  ...
)
```

**AI associate is the most restricted role:** scoped to the active task only. No broad matter dump. No historical cross-ref without a **new access grant per task**.

Implementation: `backend/privilege/access_control.py`.

---

## 4. Data segregation

```
/tenant/{firm_id}/
  /matter/{matter_id}/
    /privileged/          ← KMS: matter-specific
      /communications/
      /advice_drafts/
      /strategy_notes/
    /non_privileged/      ← KMS: tenant-wide
      /filings/
      /public_docs/
      /correspondence_third_party/
```

| Isolation | Rule |
|-----------|------|
| Firm | Separate encrypted tenant |
| Matter | Logical partition within tenant |
| Privileged docs | Separate storage key prefix |
| Encryption | Matter-scoped keys for privileged material |
| Key rotation | Target 90 days; old keys decrypt-only |
| Plaintext | No privileged plaintext on shared multi-tenant GPU/log sinks |

Phase 1: path layout + key prefix helpers only. Production KMS integration is Phase 2.

---

## 5. Waiver prevention — production gate

Mandatory before **any** document leaves the system (export, opposing production, tribunal filing):

1. Privilege scan on export set  
2. If any doc is `CLAIMED` or `ASSERTED` (or `UPHELD` unless waived):  
   - **BLOCK** export  
   - Route to privilege review queue  
   - Require **instructing_lawyer** cryptographic sign-off  
3. If waiver intended:  
   - Require **client_principal** cryptographic sign-off  
   - Append `waiver_event` (timestamp, actor, basis, scope)  
4. Tribunal filing uses the **same** gate — court destination does not bypass privilege  

### Clawback

If post-production privilege discovery:

- Log what / when / to whom / who authorized  
- Generate clawback letter **template**  

**Template note:** Map to current BC Supreme Court Civil Rules (verify rule number and form before filing; do not treat a hardcoded rule cite as authority without checking the official Rules).

Implementation: `backend/privilege/production_gate.py`.

---

## 6. Audit & chain of custody

Append-only, tamper-evident log:

| Event | Fields |
|-------|--------|
| Privileged access | timestamp, actor_id, action, document_id, matter_id, ip_hash |
| Status change | timestamp, actor_id, old→new, reason, auth_method |

| Retention (targets) | |
|---------------------|--|
| Audit logs | 10 years (align with Law Society BC record-retention practice — confirm current guidance) |
| Privileged docs | Client retention policy; never silent auto-delete |
| “Deletion” | Prefer key destruction (crypto shred) over naive file delete |

---

## 7. Law Society of BC — rule mapping (hooks)

| Hook | Architecture response |
|------|------------------------|
| Confidentiality (Code ch. on confidential information / client secrets — verify current Code numbering) | Access control + encryption + audit |
| Technology competence | This design + training + human gates = competence record |
| Trust accounting | Out of scope for privilege layer; Phase 2 flag |
| Innovation Sandbox (if public-facing AI assistance) | Privilege layer is a core compliance argument: no AI access to unscoped privileged material; HITL &lt; 0.85; production gate |

**Do not treat this mapping as legal advice.** Confirm against current *Code of Professional Conduct for British Columbia* and LSBC technology guidance before relying in a competence or sandbox filing.

---

## 8. Honest limitations

- Does **not** replace lawyer judgment on privilege calls  
- Does **not** stop a determined insider with legitimate access (screenshots) — logs only  
- Does **not** auto-map multi-jurisdiction privilege (BC ≠ ON ≠ US)  
- Does **not** give legal advice — AI retrieves/processes; advice is a lawyer function  

---

## 9. Phase 1 deliverable checklist

| Deliverable | Location | Status |
|-------------|----------|--------|
| Domain model + state machine | `privilege_schemas.py`, `state_machine.py` | Done |
| Classifier rule + annotation spec | `privilege_classifier_spec.md` | Spec done; model not trained |
| Access control schema | `access_control.py` | Done |
| Production gate | `production_gate.py` | Done |
| Law Society mapping | this document §7 | Done |
| KMS / physical segregation | design only | Phase 2 |
| NLI fine-tune | design only | Phase 2 |

Estimated full production hardening: **4–6 weeks** with a legal technologist reviewing classification rules (as product plan, not a commitment).

---

## 10. Recommended next build

**Evidence Matrix (Layer 2)** is the next product value slice for messy RTB files.  
In parallel, deepen **classifier annotation schema** if you are about to label a communications corpus.

Both are needed; Evidence Matrix ships client-visible value faster. Classifier quality is a privilege-safety critical path before any multi-user production.
