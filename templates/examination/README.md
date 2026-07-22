# Examination outlines

Source-linked cross / chief examination planning.

```python
from templates.examination.demo_landlord_rep_cross import demo_landlord_rep_cross
from backend.matters import create_matter

s = create_matter("Hearing prep", matter_id="m1")
path = s.install_demo_landlord_rep_cross_template()
print(s.load_examination_outline("EXAM-CROSS-DEMO-001").format_outline())
```

Legacy alias `install_sanghera_cross_template()` re-exports the **synthetic** demo only.

Each question should cite:
- Transcript pin (`[MM:SS]` + optional quote)
- and/or Evidence node id (`EM-019` / `EV-…`)

**Not legal advice.** Confirm quotes against the official transcript before hearing.
**SYNTHETIC DEMO ONLY** — no real parties or file numbers.
