# Evidence Matrix (Option A)

Matter-scoped factual backbone: ingest → matrix rows → gaps / links / chronology.

```python
from pathlib import Path
from backend.evidence import EvidenceMatrix, ingest_bytes, format_chronology_markdown
from backend.evidence.crossref import detect_temporal_conflicts

m = EvidenceMatrix("demo-matter", root=Path("matters"))
ingest_bytes(m, filename="20251128_mold.jpg", data=open("photo.jpg","rb").read(),
             human_notes="back unit mold", location="990A")
print(m.gap_report(["mold_hazard", "retaliatory_eviction"]))
print(format_chronology_markdown(m.all()))
```

See `architecture/EVIDENCE_MATRIX.md`. Do not store real client files in a public Space.
