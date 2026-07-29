# Hugging Face Setup

This guide sets up Hugging Face assets for BC Legal AI from `D:\AI legal\bc-legal-ai`.

## 1. Install CLI

```powershell
pip install -U huggingface_hub
hf --help
```

## 2. Create a write token

Create a Hugging Face token at:

```text
https://huggingface.co/settings/tokens
```

Use the minimum required permissions for the operation.

Set it for the current PowerShell session:

```powershell
$env:HF_TOKEN = "hf_..."
```

Do not commit tokens to git.

## 3. Login

```powershell
hf auth login --token $env:HF_TOKEN --add-to-git-credential
hf auth whoami
```

## 4. Asset IDs

Default public assets:

```text
Space:   dmang69/bc-legal-ai
Dataset: dmang69/bc-legal-ai
URL:     https://dmang69-bc-legal-ai.static.hf.space
```

The public Space is static and synthetic-only.

## 5. Public Space policy

The public Space must not accept or store:

- real client files;
- litigation records;
- privileged communications;
- court file numbers from live matters;
- RTB file numbers from live matters;
- private addresses or names.

## 6. Local source folders

```text
huggingface-space/      Public static Space source
huggingface/            HF asset control workspace
skills/                 Skill packs for dataset publication
lexicon/                Glossary materials
legislation/            Official-source extracts and verification logs
```

## 7. Validate before publishing

```powershell
python scripts\validate-huggingface-assets.py
python -m pytest tests
```
