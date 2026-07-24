# Pre-deployment checklist — public static demo

**Target Space:** https://huggingface.co/spaces/Dmang69/bc-legal-ai-demo  
**Source:** `huggingface-space-static/`  
**Workflow:** `.github/workflows/deploy-hf-space.yml`  
**Demo version:** static-v1.1

## Design lock (six corrections) — verified in demo

| # | Rule | Status in static demo |
|---|------|------------------------|
| 1 | Consent ≠ privilege | Guardrails + Consent tab |
| 2 | Withdrawal ≠ unconditional deletion (PIPA reasonable notice; retain holds) | Guardrails + Consent tab |
| 3 | Form **66** petition; **67** response; interlocutory ~**32**/**33**; affidavit **109** | Guardrails + JR clock output |
| 4 | JR: **60 days from issuance**; ATA s.57(2) extension; alternatives when uncertain | JR clock tab (local calendar math) |
| 5 | Honest E2EE (on-device **or** controlled server decrypt — not both) | Demo is on-device JS; guardrail text |
| 6 | RTB archive = published subset, not complete corpus | Guardrails + footer + CanLII blurb |

## Code quality gates (done in repo)

- [x] Timezone-safe JR date arithmetic (no `toISOString` day shift)
- [x] Invalid calendar dates rejected (`2026-02-31`)
- [x] Uncertain mode labels result as **candidate**, not confident filing date
- [x] HITL note on JR clock
- [x] Mild PII screen (email / NA phone with separators / Canadian postal)
- [x] Fail-closed disclaimer; no statute text generated from weights
- [x] Space README YAML: `sdk: static`, emoji ⚖️, version note
- [x] Deploy workflow deletes leftover `style.css` / Gradio files on upload
- [x] Path-filtered GH Action only on `huggingface-space-static/**`

## Operator steps before / during first live deploy

1. **GitHub secret `HF_TOKEN`**
   - Create **Write** token: https://huggingface.co/settings/tokens  
   - Repo → Settings → Secrets and variables → Actions → `HF_TOKEN`

2. **HF account able to host static Spaces**
   - Space `Dmang69/bc-legal-ai-demo` already exists with `sdk: static` (confirmed via API).
   - If Actions get **402**, complete HF email verification / billing method on file (static is free; create may still 402 without it).

3. **Deploy**
   - Preferred: push to `main` (this folder) **or** Actions → **Deploy HF Space (static demo)** → Run workflow  
   - Or manual CLI from repo root:
     ```bash
     hf upload Dmang69/bc-legal-ai-demo huggingface-space-static . --repo-type space \
       --commit-message "deploy static-v1.1"
     ```

4. **Post-deploy smoke (live Space)**
   - Open https://huggingface.co/spaces/Dmang69/bc-legal-ai-demo  
   - Page source / DOM should show `static-v1.1` (not the default “Welcome to your static Space!” template)  
   - **Triage:** one-month notice + “judicial review” → Form 66 + 60-day note  
   - **JR clock:** `2026-06-15` + all boxes confirmed (not sous review) → deadline **2026-08-14**, MODE ORDINARY  
   - **JR clock uncertain:** uncheck finality → MODE ALTERNATIVES REQUIRED + candidate labeling  
   - **PII:** email in triage → rejected  
   - **Guardrails tab:** all six items visible  

5. **Do not ship if**
   - Live page is still HF default `index.html` / `style.css` template  
   - JR eng still uses UTC `toISOString`  
   - Form 67 presented as commencing petition  
   - Archive absence called “no decision exists”  
   - Claims of E2EE + unrestricted server AI appear anywhere on the public page  

## Out of scope for this public static deploy

- Private backend, real matters, OCR, court-ready export  
- Gradio / model weights Space (needs HF PRO + legal risk review)  
- GitLab wiki CI or monorepo production k8s  

## Rollback

- Re-upload previous commit of `huggingface-space-static/` or restore Space files from HF commit history.  
- Or point docs to legacy landing: https://huggingface.co/spaces/Dmang69/bc-legal-ai
