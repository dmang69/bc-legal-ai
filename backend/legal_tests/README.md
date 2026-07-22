# Legal tests

## DISABLED: RTA-s56-retaliatory-eviction (Priority Zero — 2026-07-21)

```text
id: RTA-s56-retaliatory-eviction
status: DISABLED
reason: Incorrect statutory mapping.
```

On the current **Residential Tenancy Act** (confirm on **BC Laws**):

- **s. 56** is about a **landlord application for an order ending a tenancy early** — not a multi-element civil “retaliatory eviction” burden-shift test as previously encoded.
- Retaliation language elsewhere (e.g. offence provisions historically associated with **s. 95(2)** — re-check numbering on BC Laws) does **not** automatically authorize the old element list.

### Behaviour

```python
from architecture.legal_test import rta_s56_retaliatory_eviction_test, LegalTestDisabledError
from backend.legal_tests import evaluate_legal_test

t = rta_s56_retaliatory_eviction_test()
assert t.disabled is True
# evaluate_legal_test(t, nodes)  → raises LegalTestDisabledError
```

### Replacement requirements

A new lawyer-approved test must store:

- effective_from / effective_to  
- source snapshot (BC Laws currency line)  
- verified_by / review_date  
- authority_status = LAWYER_APPROVED  
- correct separation of: statutory offence · RTB remedy · improper purpose · HRC · JR grounds  

**CIT-RTA-S56** is marked **REJECTED** for retaliation use (early-end / landlord application tags only).
