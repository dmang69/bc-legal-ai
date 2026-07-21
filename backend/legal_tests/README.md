# Legal tests

## RTA s.56 retaliatory eviction

```yaml
id: RTA-s56-retaliatory-eviction
source: Residential Tenancy Act, SBC 2002, c. 78, s. 56
elements:
  E1-timely-dispute     # procedural, required — 15 days
  E2-prior-complaint    # substantive, required — protected activity
  E3-temporal-nexus     # inferential, required, weight 0.30
  E4-absence-legitimate-cause  # inferential, optional, weight 0.40
burden_shift: E1+E2+E3 → landlord must show non-retaliatory cause
```

```python
from backend.legal_tests import rta_s56_retaliatory_eviction_test, evaluate_legal_test

test = rta_s56_retaliatory_eviction_test()
ev = session.evaluate_legal_test("RTA-s56-retaliatory-eviction")
if ev.burden_shift_triggered:
    print(ev.reasoning_chain_flags)  # BURDEN_SHIFT_TO_LANDLORD
```

**Verify** s. 56 and adverse cases on BC Laws / CanLII before filing.  
`CIT-RTA-S56` is PARTIALLY_VERIFIED until official exact text is registered.  
Adverse authorities (Preston / Yu labels) are **UNVERIFIED** illustrative notes only.
