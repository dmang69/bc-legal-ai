# Privilege classifier — training & annotation schema

First-pass filter only. **Does not** decide privilege for production without human confirmation when confidence &lt; 0.85 or borderline facts.

## Labels

| Label | Use |
|-------|-----|
| `privilege_basis` | solicitor_client \| litigation \| settlement_implied \| none |
| `advice_sought` | bool |
| `advice_given` | bool |
| `litigation_contemplated` | bool |
| `sender_role` | client \| lawyer \| third_party \| unknown |
| `recipient_role` | same |
| `needs_human_review` | bool (annotator override) |

## Annotation unit

One communication artifact (email message, SMS thread segment, chat turn group, letter, transcript excerpt).

```json
{
  "artifact_id": "uuid",
  "matter_id": "uuid",
  "text": "...",
  "channel": "email|sms|chat|letter|voice_transcript",
  "sender_role_gold": "client",
  "recipient_role_gold": "lawyer",
  "advice_sought_gold": true,
  "advice_given_gold": false,
  "litigation_contemplated_gold": true,
  "privilege_basis_gold": "solicitor_client",
  "annotator_id": "id",
  "notes": "borderline because cc'd property manager",
  "jurisdiction": "BC"
}
```

## Decision rules (annotator guidance)

1. Client ↔ lawyer + legal advice sought or given → strong `solicitor_client` candidate.  
2. Third party on the channel → often **none** or partial; **always** `needs_human_review`.  
3. Pure logistics (“see you at 3”) without advice → usually `none`.  
4. Settlement discussions may be `settlement_implied` (jurisdiction-specific — lawyer confirms).  
5. When unsure → `needs_human_review` and **do not** auto-finalize.

## Evaluation metrics (before any production deploy)

- Precision on `none` when true privilege exists (**critical** — false none → waiver risk)  
- Recall on privileged classes  
- Calibration of confidence vs human confirmation rate  
- Adversarial: prompt injection in body of “evidence” emails  

## Corpus plan

| Source | Care |
|--------|------|
| Synthetic dialogues | Safe to open-source patterns |
| Real firm mail | Consent + de-id + privilege protocol; never public |
| Public filings only | Not privileged training for SC privilege |

## Model stack (future)

- Role resolution: rules + entity linking  
- Advice NLI: fine-tuned encoder on annotated legal comms  
- Stage 3: human gate mandatory below 0.85  
