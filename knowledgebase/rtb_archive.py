"""
RTB decision archive limitations.

The official BC archive covers specific historical publication ranges and categories.
Absence from the archive is not proof that no decision exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from architecture.contracts.models import RTB_ARCHIVE_WARNING, RtbDecisionContract


@dataclass
class RtbArchiveLookupResult:
    found: bool
    decision: Optional[RtbDecisionContract]
    warning: str = RTB_ARCHIVE_WARNING
    # Critical: never treat not-found as non-existence
    absence_proves_nonexistence: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "found": self.found,
            "decision": self.decision.to_dict() if self.decision else None,
            "warning": self.warning,
            "absence_proves_nonexistence": False,
            "ui_message": (
                "No matching decision in the loaded archive subset. "
                + RTB_ARCHIVE_WARNING
            ),
        }


def lookup_rtb_decision(
    *,
    citation_or_file: str,
    catalog: Optional[dict[str, RtbDecisionContract]] = None,
) -> RtbArchiveLookupResult:
    catalog = catalog or {}
    key = (citation_or_file or "").strip().lower()
    for k, v in catalog.items():
        if k.lower() == key or v.citation_or_file.lower() == key:
            return RtbArchiveLookupResult(found=True, decision=v)
    return RtbArchiveLookupResult(found=False, decision=None)
