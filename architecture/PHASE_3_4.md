# Phase 3–4 Architecture (implementation map)

**Operating rule:** The model proposes → evidence verifies facts → authority verifies law → rules verify procedure → privilege controls disclosure → qualified human approves.

## Six design locks

1. **Consent ≠ privilege** — processing authorization only; never auto-creates/waives privilege.  
2. **Withdrawal ≠ unconditional deletion** — optional AI blocked immediately; PIPA reasonable notice; holds/legal bases assessed separately ([PIPA on BC Laws](https://www.bclaws.gov.bc.ca/civix/document/id/consol16/consol16/00_03063_01)).  
3. **Form 66 petition; Form 67 response** — Rule 16-1; interlocutory Form 32/33; affidavit Form 109 ([SCR](https://www.bclaws.gov.bc.ca/civix/document/id/lc/statreg/168_2009_02)).  
4. **JR clock: 60 days from final decision issuance** — alternatives when uncertain; ATA s.57(2) extension is counsel pathway ([ATA](https://www.bclaws.gov.bc.ca/civix/document/id/consol13/consol13/04045_01)).  
5. **No E2EE + server AI dual claim** — Model A or Model B, honest labels.  
6. **RTB archive incomplete** — absence ≠ non-existence ([decision archive](https://www2.gov.bc.ca/gov/content/housing-tenancy/residential-tenancies/decision-search)).

## Phase 3 API / DB contract (next artifact — done)

→ **`architecture/contracts/PHASE_3_API_DB_CONTRACT.md`**  
→ SQL: `architecture/contracts/sql/phase3_core.sql`  
→ OpenAPI: `architecture/contracts/openapi/phase3_hitl.yaml`  
→ Validators: `architecture/contracts/models.py`

## HITL control plane

```text
services/reasoning/hitl/
├── consent/           # purpose-specific; evaluate; PIPA-aware withdrawal
├── exceptions/        # taxonomy; freeze; human resolve
├── privilege_check/   # freeze / two-pro / signed manifest
├── competency_gate/
├── approvals/
├── escalation/
├── schemas/
└── control_plane/
```

## Deadlines

`services/deadlines/jr_clock.py` — STANDARD_60_FROM_ISSUANCE + uncertainty modes + ATA s.57(2) path.

## Production readiness

Not production-ready until Layers 0–2, audit, auth, UPL compliance, and eval suite land. **No real client documents on public Hugging Face Spaces.**
