# Hugging Face Publishing

## Public deterministic Gradio Space

Publish the Gradio Space from:

```text
huggingface-space/
```

Expected public URL:

```text
https://dmang69-bc-legal-ai.hf.space
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

`Dmang69/bc-legal-ai-base` is documentation-only unless and until it contains a complete standard Transformers checkpoint. Never set `model_type` to a policy-card identifier and never recommend `trust_remote_code=True` as a substitute for missing configuration, tokenizer, model class, or weights.

A deployable standard base for this project is `Qwen/Qwen2.5-7B-Instruct`, pinned to a reviewed immutable commit. Private inference must use `AutoTokenizer` and `AutoModelForCausalLM` with `trust_remote_code=False`. Copying base files to another repository does not create a legally fine-tuned model and must preserve licence, attribution, and architecture identity.

Do not publish a checkpoint or LoRA adapter until:

- dataset provenance and licence review are complete;
- confidential-data scan passes;
- complete config/tokenizer/weights or adapter assets are present;
- base model, revision, licence, and intended task are documented;
- legal golden-set and safety evaluations pass;
- model card states that verified retrieval remains required;
- post-upload loading is verified at the exact published commit.

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
  src="https://dmang69-bc-legal-ai.hf.space"
  frameborder="0"
  width="850"
  height="450"
></iframe>
```
