---
title: BC Legal AI Associate
emoji: ⚖️
colorFrom: blue
colorTo: gray
sdk: static
pinned: false
license: mit
short_description: Deterministic BC tenancy/JR triage demo — not legal advice
app_file: index.html
---

# BC Legal AI Associate — public demo (static, client-side)

Deterministic demonstration for the **BC Legal AI Associate** project. No model
inference. No statute text from memory. All logic runs **in the visitor's
browser** (on-device — consistent with design correction #5).

**Space:** https://huggingface.co/spaces/Dmang69/bc-legal-ai  
**Demo version:** static-v1.2

## Features

- **Matter triage** — notice-type deadline flags + forum routing
- **JR limitation clock** — 60 days from issuance (ATA s.57(1)) with s.57(2)
  extension awareness and alternatives mode when finality/date/Act/review status
  is uncertain (timezone-safe local calendar math)
- **Analytical tagger** — FACT / ALLEGATION / ASSUMPTION / LEGAL ARGUMENT /
  RECOMMENDATION decomposition
- **Design guardrails** — the six locked corrections, displayed for auditability
- **Official legislation** — fail-closed links to BC Laws, ATA, PIPA, court forms
- **RTA pin self-check** — common wrong-memory section pins

**Not a lawyer. Not legal advice.**  
**Do not upload confidential** client or litigation files to this public Space.  
Use synthetic data only.

Private product (GitHub) adds Puter AI base, OpenClaw agents, Kimi, and Arena AI —
those require a private backend and are **not** enabled on this public Space.

## Locked design guardrails (encoded in this demo)

1. **Consent is not privilege** — consent authorizes specified processing; it never creates, waives, or determines privilege.
2. **Consent withdrawal ≠ unconditional deletion** — under BC PIPA, withdrawal operates on reasonable notice; retention, legal-hold, and evidentiary obligations are assessed separately. Future optional AI access can be revoked immediately.
3. **Form 66** commences a petition (Form 67 is the response); interlocutory applications generally use **Form 32** (Form 33 response); affidavits may use **Form 109**.
4. **JR clock: 60 days from issuance** of the final decision (ATA s.57(1)), with the **s.57(2)** extension power; alternatives are required when finality, date, enabling Act, or post-decision review status is uncertain — no single date is filing-safe until confirmed.
5. **Honest encryption**: on-device classification *or* controlled server-side decryption with consent and disclosure — never both claims at once. (This static demo is the on-device posture.)
6. **The RTB decision archive is a published subset**, not a complete corpus; absence from the archive is never proof that no decision exists.

## Links

- **This Space:** https://huggingface.co/spaces/Dmang69/bc-legal-ai
- **GitHub:** https://github.com/dmang69/bc-legal-ai
- **Dataset:** https://huggingface.co/datasets/Dmang69/bc-legal-ai
- **Model documentation:** https://huggingface.co/Dmang69/bc-legal-ai-base
- **BC Laws (official statute text):** https://www.bclaws.gov.bc.ca/
- **Source path in monorepo:** `huggingface-space-static/`
