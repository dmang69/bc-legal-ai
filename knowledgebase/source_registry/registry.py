"""Legal source registry — register before ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SourceAuthority:
    source_id: str
    name: str
    authority_type: str  # OFFICIAL_PRIMARY | SECONDARY
    jurisdiction: str
    permitted_content: list[str]
    retrieval_method: str = "approved_connector"
    terms_reviewed_at: Optional[str] = None
    last_successful_update: Optional[str] = None
    health_status: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "authority_type": self.authority_type,
            "jurisdiction": self.jurisdiction,
            "permitted_content": list(self.permitted_content),
            "retrieval_method": self.retrieval_method,
            "terms_reviewed_at": self.terms_reviewed_at,
            "last_successful_update": self.last_successful_update,
            "health_status": self.health_status,
        }


def _seed() -> list[SourceAuthority]:
    return [
        SourceAuthority(
            source_id="source_bc_laws",
            name="BC Laws",
            authority_type="OFFICIAL_PRIMARY",
            jurisdiction="BC",
            permitted_content=[
                "statutes",
                "regulations",
                "court_rules",
                "point_in_time_versions",
            ],
            health_status="HEALTHY",
        ),
        SourceAuthority(
            source_id="source_bc_courts",
            name="BC Courts",
            authority_type="OFFICIAL_PRIMARY",
            jurisdiction="BC",
            permitted_content=["judgments", "practice_directions", "forms"],
        ),
        SourceAuthority(
            source_id="source_rtb_official",
            name="Residential Tenancy Branch (official)",
            authority_type="OFFICIAL_PRIMARY",
            jurisdiction="BC",
            permitted_content=["rules", "forms", "policy_guidelines", "decisions"],
        ),
        SourceAuthority(
            source_id="source_canlii",
            name="CanLII",
            authority_type="SECONDARY",
            jurisdiction="CA",
            permitted_content=["cases", "citation_relationships"],
            health_status="MANUAL_REQUIRED",
        ),
    ]


@dataclass
class SourceRegistry:
    sources: list[SourceAuthority] = field(default_factory=_seed)

    def get(self, source_id: str) -> Optional[SourceAuthority]:
        for s in self.sources:
            if s.source_id == source_id:
                return s
        return None

    def primary_only(self) -> list[SourceAuthority]:
        return [s for s in self.sources if s.authority_type == "OFFICIAL_PRIMARY"]
