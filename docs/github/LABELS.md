# GitHub label system

Create before opening Phase 4 issues (`gh label create` or GitHub UI).

## Workstream

```text
area:security
area:identity
area:matters
area:conflicts
area:consent
area:privilege
area:ingestion
area:ocr
area:evidence
area:chronology
area:knowledge
area:retrieval
area:citations
area:legal-tests
area:model
area:fine-tuning
area:agents
area:hitl
area:deadlines
area:procedure
area:drafting
area:exports
area:client-portal
area:windows
area:post-resolution
area:enforcement
area:judicial-review
area:retention
area:infrastructure
area:devops
area:testing
area:compliance
```

## Issue type

```text
type:epic
type:feature
type:bug
type:security
type:legal-review
type:research
type:test
type:documentation
type:migration
type:infrastructure
```

## Priority

```text
priority:P0-critical
priority:P1-high
priority:P2-medium
priority:P3-later
```

## Status

```text
status:blocked
status:ready
status:in-progress
status:human-review
status:legal-review
status:security-review
status:completed
```

## Risk

```text
risk:privilege
risk:confidentiality
risk:deadline
risk:legal-accuracy
risk:cross-matter
risk:data-loss
risk:unauthorized-practice
```

## Bulk create (after `gh auth login`)

```bash
# example
gh label create "priority:P0-critical" --color B60205 --description "M0 / blocking"
```

Or run: `python scripts/create_github_labels.py` (requires `gh`).
