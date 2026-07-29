# Hugging Face Workspace — BC Legal AI

This folder is the repository control plane for Hugging Face assets connected to `dmang69/bc-legal-ai`.

## Asset map

| Asset type | Folder | Intended HF target | Real client data? |
|---|---|---|---|
| Spaces | `spaces/` | `dmang69/bc-legal-ai` and future private Spaces | Public Space: no; private Space: only after gates |
| Datasets | `datasets/` | `dmang69/bc-legal-ai` dataset repos | No live matters; synthetic/reference materials only |
| Models | `models/` | future LoRA/adapter/model cards | No training on confidential data |
| Storage buckets | `buckets/` | future HF Storage / private object storage plans | Real data only in private encrypted environment |
| Docs | `docs/` | HF setup, tokens, publishing, governance | No secrets |
| Config | `config/` | repo IDs and publish configuration templates | No tokens |

## Current public Space

Static public Space URL:

```text
https://dmang69-bc-legal-ai.static.hf.space
```

Embed snippet:

```html
<iframe
  src="https://dmang69-bc-legal-ai.static.hf.space"
  frameborder="0"
  width="850"
  height="450"
></iframe>
```

## Hard rule

Do not put real client, litigation, privileged, or live matter data in public Hugging Face assets.
