# Data Pipeline — BC Laws + RTB + JR

## Source gates

```
IF content_type == "bc_statute_or_reg":
    source MUST BE bclaws.gov.bc.ca
    record currency_line + accessed_on
    optional: historical version for event_date

IF content_type == "rtb_decision":
    source MAY BE canlii.org (or official RTB publication)
    extract cited RTA sections → RE-VERIFY each pin on BC Laws

IF content_type == "judicial_review_or_appeal":
    source MAY BE canlii.org or courts.gov.bc.ca / scc-csc.ca
    do NOT replace statute text with paraphrases in reasons
```

## Stages

1. **Fetch** — BC Laws HTML/PDF; CanLII decision API/HTML  
2. **Normalize** — section-aware chunking; strip nav chrome  
3. **Metadata** — currency, access date, citation, version_kind  
4. **Pin audit** — map any cited sections to live BC Laws  
5. **Pair build** — instruction/response with CONTEXT blocks  
6. **Eval suite** — currency traps, wrong-section traps, refusal tests  
7. **Index** — vector store for RAG (separate collections: laws / rtb / jr)  
8. **Train (optional)** — LoRA SFT on pairs that always include official context  

## Wrong-section regression (must pass)

| Query topic | Must not answer | Must answer (if verified) |
|-------------|-----------------|---------------------------|
| Cannot contract out | s. 6 | s. 5 |
| Quiet enjoyment | s. 22 | s. 28 |
| Entry hours | 9 a.m.–9 p.m. only | 8 a.m.–9 p.m. under s. 29 |

Update tests whenever BC Laws consolidation changes.

## Refresh cadence

| Corpus | Cadence |
|--------|---------|
| BC Laws | Before every production release + weekly job |
| RTB CanLII | Weekly incremental |
| JR CanLII | Weekly incremental |
