# Contributing to BC Legal AI

## Scope

This repository contains:

- Phase 1: Working Gradio demo (no inference)
- Phase 2–4: Architectural designs and roadmaps

## Before you start

**Read these first:**

- `README.md` — What this is (and isn't)
- `ARCHITECTURE_AUDIT.md` — Current state
- `PHASE_3_ROADMAP.md` — Phase 3 detailed spec
- `PHASE_4_ROADMAP.md` — Phase 4 detailed spec

**Then read the law:**

- [Law Society of British Columbia — Unauthorized Practice of Law](https://www.lawsociety.bc.ca/for-the-public/unauthorized-practice-of-law/what-is-unauthorized-practice-of-law/)
- [BC Personal Information Protection Act](https://www.bclaws.gov.bc.ca/civix/document/id/consol16/consol16/00_03063_01)
- [Residential Tenancy Act, SBC 2002, c 78](https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01)

## Contributing principles

1. **Never hallucinate law.** Every legal citation must trace to BC Laws, CanLII, or official RTB sources.
2. **Never skip the human.** Approvals, reviews, and privilege determinations require qualified lawyers.
3. **Never assume correctness.** Test everything; assume the system will fail.
4. **Never confuse phases.** Phase 1 (demo) ≠ Phase 3 (reasoning engine). Don't merge them.
5. **Never ignore regulatory boundaries.** Consult LSBC, privacy counsel, and security review before handling real client data.

## What we need

### Phase 2 (Document Ingestion)

- OCR pipeline with confidence scoring
- Document classifier
- Metadata extractor
- Deduplication engine
- Email/cloud-storage connectors

### Phase 3 (HITL & Knowledge Base)

- Consent service
- Exception logger
- Privilege gate
- Competency checker
- BC Laws ingestion pipeline
- Citation verifier
- Template versioning

### Phase 4 (Client Platform)

- MFA authentication
- Matter isolation
- Client portal
- Secure messaging
- Post-resolution tracking
- Enforcement generator
- JR pipeline
- Retention scheduler

## How to contribute

1. **Pick a Phase.** Don't jump ahead; Phase 1 doesn't depend on Phase 4.
2. **Create a branch:** `git checkout -b phase-N-feature-name`
3. **Build the service.** Reference the roadmap.
4. **Write tests.** Assume the system will be used by real clients.
5. **Document it.** Link back to the architectural spec.
6. **Open a PR.** Describe what phase and acceptance criteria it meets.
7. **Legal review.** Have a lawyer read it before merging.

## Testing requirements

Before Phase 3 merge:

- ✅ No statute quotes from model weights
- ✅ All legal citations verify
- ✅ Privilege gates block unsanctioned release
- ✅ Consent is independent from privilege

Before Phase 4 merge:

- ✅ Cross-matter data isolation
- ✅ MFA enforcement
- ✅ Deadline calculation matches rules
- ✅ Accessibility tests (WCAG, screen reader, multi-language)

## Code style

- Python: Black formatter, 88-char line limit
- Docstrings: Describe purpose, inputs, outputs, exceptions
- Comments: Explain legal requirements, not obvious code
- Git: Descriptive commit messages, link to spec

## Deployment

**Phase 1** can deploy to public Hugging Face Space (CPU-only demo).

**Phase 2+** require private infrastructure (auth, encryption, audit logs).

**Phase 4** requires Law Society Innovation Sandbox clearance or equivalent authorization before handling real client data.

## Contact

For regulatory questions: consult LSBC directly ([lawsociety.bc.ca](https://www.lawsociety.bc.ca/))

For technical questions: open an issue.
