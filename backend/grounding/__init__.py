"""GroundingGate — fail-closed claim validation."""

from backend.grounding.citation_db import CitationDB, seed_bc_workbench_citations
from backend.grounding.gate import GroundingGate, build_gate_for_nodes

__all__ = [
    "CitationDB",
    "GroundingGate",
    "build_gate_for_nodes",
    "seed_bc_workbench_citations",
]
