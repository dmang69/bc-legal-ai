# Architecture decision: modular monolith (V1)

**Status:** Accepted (Phase 4 controlling program, 2026-07-22)  
**Supersedes:** “microservices per layer” as the **default** starting topology.

## Decision

Ship V1 as a **modular monolith** (single FastAPI process / deployable unit) with **background workers** consuming a Redis-backed (or equivalent) job queue. Domain code lives in clear modules (`identity`, `matter`, `consent`, `privilege`, `ingestion`, `evidence`, `knowledge`, `citation`, `deadline`, `drafting`, `export`, `audit`).

## Rationale

Starting with many microservices increases:

- deployment and ops complexity;
- authorization and privilege-boundary risk;
- distributed logging and tracing cost;
- transaction inconsistency risk;
- time-to-M1 and operational cost.

The repository’s `services/` packages are **domain modules** (and job entrypoints), not independent production services, until split criteria are met.

## Split criteria (only then extract a service)

Extract a module to its own deployable **only if** one or more hold:

1. Independent scaling is required  
2. A hard security boundary requires process isolation  
3. Processing must run in an isolated environment (e.g. untrusted OCR sandbox)  
4. Release schedules conflict  
5. The module already has a stable API contract used by multiple consumers  

## Data plane (V1)

| Store | Role |
|-------|------|
| PostgreSQL | system of record + relationship tables |
| pgvector | embeddings |
| S3-compatible | blobs |
| Redis | queue + short cache + rate limits |

**Not required for V1:** Neo4j, dedicated time-series database.

Graph-like data: `*_relationships` tables + recursive SQL until proven insufficient.  
Audit: append-only PostgreSQL + hash chain + optional WORM export.

## Related

- Controlling program: `docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md`  
- Workers: OCR, transcription, knowledge updates, rendering, evaluation  
