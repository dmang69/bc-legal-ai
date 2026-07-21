# Examination outlines

Source-linked cross / chief examination planning.

```python
from templates.examination.sanghera_cross_outline import sanghera_cross_outline
from backend.matters import create_matter

s = create_matter("Hearing prep", matter_id="m1")
path = s.install_sanghera_cross_template()
print(s.load_examination_outline("EXAM-CROSS-SANGHERA-001").format_outline())
```

Each question should cite:
- Transcript pin (`[MM:SS]` + optional quote)
- and/or Evidence node id (`EM-019` / `EV-…`)

**Not legal advice.** Confirm quotes against the official transcript before hearing.
