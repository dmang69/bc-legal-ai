# Windows connector — security boundary (M6)

**Status:** Binding design constraint for any desktop / Windows file integration.

## Forbidden

- Silent whole-drive indexing  
- Silent whole-user-profile indexing  
- Indexing files belonging to other clients/matters without explicit selection  
- Marketing “Windows Search integration” as unrestricted OS-wide search  

## Required flow

```text
User explicitly selects an approved folder
    ↓
Local connector inventories metadata only
    ↓
Privilege and consent gate
    ↓
User previews and confirms selected documents
    ↓
Encrypted upload and/or local processing
    ↓
Matter-scoped indexing only
```

## Required controls

| Control | Requirement |
|---------|-------------|
| Approved folders | User-configured allowlist only |
| Exclusion list | Configurable local exclusions |
| Preview | Before import |
| Duplicates | Detect before/after transfer |
| Consent | Explicit confirmation recorded |
| Privilege | Classification before/during import |
| Provenance | Source path retained on matter |
| Revocation | Connector access revocable |
| Audit | Local connector audit log |
| Credentials | OS credential protection (no plaintext secrets in repo) |
| High confidentiality | Prefer on-device OCR, classification, redaction before any network transfer |

## Dependencies

- M1 matter isolation and consent  
- M2 quarantine and Evidence Matrix  
- No real client material through the connector until M1 and M2 pass  

See controlling program: `docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md` §1.5 / M6.
