# Agents

Limited-responsibility stages. **Not** autonomous filers or senders.

| Module | Agent |
|--------|--------|
| `intake.py` | Intake Associate |
| `evidence.py` | Evidence Analyst |
| `research.py` | Research Counsel |
| `verifier.py` | Citation Clerk |
| `drafter.py` | Drafting Counsel |
| `adversary.py` | Devil’s Advocate |
| `procedural_clerk.py` | Procedural Clerk |
| `supervisor_gate.py` | Supervising Counsel Gate |

Implementations start as pure functions over `architecture.schemas` types.  
Wire models and retrieval only after matter isolation and citation gate exist.
