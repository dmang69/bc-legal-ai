# Matter isolation

Every request is scoped to a `matter_id`. Evidence matrix rows, drafts, and chat history never cross matters.

```python
from backend.matters import create_matter

s = create_matter("My RTB file", matter_id="client-a-2026", tribunal_or_court="RTB")
s.ingest_file("20251128_mold.jpg", open("photo.jpg","rb").read(), human_notes="mold")
print(s.analysis_report()["gaps"])
s.write_report()  # matters/.../analysis_report.json + chronology.md
print(s.production_check().allowed)
```

See `service.py`, `architecture/ALA_SYSTEM.md`, and `architecture/EVIDENCE_MATRIX.md`.
