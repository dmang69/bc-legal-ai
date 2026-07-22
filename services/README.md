# Microservices (Phase 2–4)

## Phase 3.1 HITL control plane

| Subsystem | Path |
|-----------|------|
| Control plane | `reasoning/hitl/control_plane/` |
| A. Consent | `reasoning/hitl/consent/` |
| B. Exceptions | `reasoning/hitl/exceptions/` |
| C. Privilege / production gate | `reasoning/hitl/privilege_check/` |
| D. Competency gate | `reasoning/hitl/competency_gate/` |
| Approvals | `reasoning/hitl/approvals/` |
| Escalation | `reasoning/hitl/escalation/` |
| Schemas | `reasoning/hitl/schemas/` |
| Upload quarantine | `client_portal/quarantine/` |

## Phase 3.2 Knowledge

| Component | Path |
|-----------|------|
| Primary sources + PIT locks | `../knowledgebase/primary_sources.py` |
| Updater + change log | `../knowledgebase/updater/` |
| Templates | `../knowledgebase/templates/` |
| Citation verifier | `../knowledgebase/citation_verifier/` |

## Phase 4

| Component | Path |
|-----------|------|
| Client portal | `client_portal/` + `../frontend/client/` |
| Messaging | `messaging/` |
| Consent center | `consent_center/` |
| Post-resolution (Layer 6 full) | `post_resolution/` — outcome_tracker, obligation_parser, compliance_monitor, escalation_router, enforcement, jr_pipeline, stay_generator, retention, destruction |
| LSBC rules scaffold | `compliance/lsbc_rules/` |
| Legacy top-level enforcement / jr / retention | `enforcement/`, `jr_pipeline/`, `retention/` (compat; prefer post_resolution/*) |

Canonical EvidenceNode: `architecture/evidence_node.py`  
Privilege middleware: `middleware/privilege_guard.py`
