# Hugging Face Storage Buckets / Object Storage

Planning area for HF Storage or alternative private object storage.

## Rule

Public Hugging Face assets must not contain real client data.

## Future bucket classes

| Bucket class | Purpose | Real data? | Required controls |
|---|---|---:|---|
| `public-demo-assets` | Static demo assets | No | Synthetic-only scan |
| `internal-fixtures` | Synthetic/redacted test files | No live data | Access control, scan |
| `private-ingestion-quarantine` | Uploaded files awaiting scan | Yes, private only | Encryption, malware scan, audit |
| `private-evidence-originals` | Immutable originals | Yes, private only | Matter keys, ACL, audit |
| `private-exports` | Approved output packages | Yes, private only | Manifest, privilege gate |

## Production note

For real matters, prefer private infrastructure with S3-compatible storage and matter-scoped encryption keys unless a HF private storage option satisfies the same controls.
