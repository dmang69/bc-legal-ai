# Legal tests

Multi-element tests (e.g. retaliatory eviction scaffold) mapped to evidence.

```python
from backend.legal_tests import retaliatory_eviction_s56_test, evaluate_legal_test
from backend.grounding.citation_db import CitationDB, seed_bc_workbench_citations

test = retaliatory_eviction_s56_test()
# test.test_id == "TEST-RETALIATORY-EVICTION-S56"
# test.elements[0].protected_activities ...

ev = evaluate_legal_test(test, nodes, citation_db=seed_bc_workbench_citations(CitationDB()))
print(ev.overall, ev.recommended_uploads)
```

**Verification:** Citation pin and element wording must be confirmed on BC Laws.  
`CIT-RTA-S56` is PARTIALLY_VERIFIED until exact text is registered.
