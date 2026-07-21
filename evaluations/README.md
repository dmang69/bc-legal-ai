# Legal evaluations

Three unit tests are not enough for legal reliability.

## Planned suites

| Suite | Path | Covers |
|-------|------|--------|
| Golden matters | `golden_cases/` | End-to-end graded files |
| Citation tests | `citation_tests/` | Fabricated case, wrong section, pinpoint |
| Deadline tests | `deadline_tests/` | Service method, holidays, deemed receipt |
| Adversarial tests | `adversarial_tests/` | Prompt injection in evidence, leakage |

## Required capabilities under test

- Fabricated-case resistance  
- Incorrect statutory-section resistance  
- Deadline and service accuracy  
- Fact / allegation separation  
- Evidence citation accuracy  
- Transcript timestamp accuracy  
- Contradiction detection  
- Adverse-authority recognition  
- Standard-of-review classification  
- Procedural-fairness analysis  
- Prompt injection inside uploaded evidence  
- Cross-matter data leakage  
- OCR failure modes  
- Incorrect quotations  
- Court-form compliance  

See `tests/` for executable unit tests of schemas and gates.

## Run structural eval suite (§7)

```powershell
python evaluations\run_eval_suite.py
```

Covers RTA section-regression map consistency, court-ready UNVERIFIED block, and statute metadata shape.
