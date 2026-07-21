# Layer 1 — Ingestion & normalization

Target pipeline: multi-format intake → zero-shot classify → OCR → NER/key-value extract → store **original** + derived text.

See `architecture/ALA_SYSTEM.md` Layer 1.  
Runtime code lands here; schemas: `IngestedDocument`, `DocTrack` in `architecture/schemas.py`.
