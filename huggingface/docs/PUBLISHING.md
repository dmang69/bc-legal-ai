# Hugging Face Publishing

## Public static Space

Publish the static Space from:

```text
huggingface-space/
```

Expected public URL:

```text
https://dmang69-bc-legal-ai.static.hf.space
```

PowerShell:

```powershell
$env:HF_TOKEN = "hf_..."
.\scripts\publish-huggingface.ps1 -Username dmang69 -DatasetName bc-legal-ai -SpaceName bc-legal-ai
```

To publish only the dataset:

```powershell
.\scripts\publish-huggingface.ps1 -Username dmang69 -SkipSpace
```

## Dataset

The public dataset may include:

- skills;
- lexicon;
- checklists;
- synthetic templates;
- allowed legislation verification logs/extracts;
- documentation.

It must not include real client or live matter data.

## Models

Do not publish LoRA adapters until:

- dataset licence review is complete;
- confidential-data scan passes;
- model card is written;
- evaluation suite passes;
- RAG-first policy is documented.

## Storage buckets

Real client data must not be placed in public HF assets.

If private HF storage is used, it must still satisfy:

- encryption;
- matter isolation;
- audit logging;
- retention policy;
- privilege controls;
- access revocation.

## Embed public Space

```html
<iframe
  src="https://dmang69-bc-legal-ai.static.hf.space"
  frameborder="0"
  width="850"
  height="450"
></iframe>
```
