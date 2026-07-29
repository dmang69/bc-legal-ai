"""
Privilege alert contracts — warn before sharing case details with non-parties.

Not legal advice. Does not determine whether privilege applies or was waived.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class PrivilegeAlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class PrivilegeAlertKind(str, Enum):
    THIRD_PARTY_DISCLOSURE = "THIRD_PARTY_DISCLOSURE"
    POSSIBLE_WAIVER_RISK = "POSSIBLE_WAIVER_RISK"
    UNPROTECTED_CHANNEL = "UNPROTECTED_CHANNEL"
    OTHER = "OTHER"


@dataclass
class PrivilegeAlert:
    """
    User-facing privilege caution.

    Example:
      ⚠ PRIVILEGE ALERT:
      Your message mentions discussing case details with a third party...
    """

    alert_id: str = field(default_factory=lambda: f"PAL-{uuid4().hex[:8]}")
    kind: PrivilegeAlertKind = PrivilegeAlertKind.THIRD_PARTY_DISCLOSURE
    severity: PrivilegeAlertSeverity = PrivilegeAlertSeverity.WARNING
    title: str = "PRIVILEGE ALERT"
    message: str = ""
    triggers: list[str] = field(default_factory=list)  # matched phrases
    third_parties_mentioned: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    block_send: bool = False  # soft warn by default; hard block optional
    requires_ack: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "kind": self.kind.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "triggers": list(self.triggers),
            "third_parties_mentioned": list(self.third_parties_mentioned),
            "recommendations": list(self.recommendations),
            "block_send": self.block_send,
            "requires_ack": self.requires_ack,
        }

    def format_alert(self) -> str:
        lines = [f"⚠ {self.title}:", self.message]
        if self.recommendations:
            lines.append("")
            lines.append("Before proceeding, consider:")
            for r in self.recommendations:
                lines.append(f"  • {r}")
        lines.append("")
        lines.append(
            "This is a privilege caution for workbench use — not a legal determination "
            "that privilege applies, does not apply, or has been waived. Ask a lawyer "
            "before sharing sensitive case information."
        )
        return "\n".join(lines)


DEFAULT_THIRD_PARTY_ALERT_MESSAGE = (
    "Your message mentions discussing case details with a third party "
    "(your neighbor). Communications with non-parties may not be protected "
    "by solicitor-client privilege. Consider whether this information "
    "should be shared before proceeding."
)

# Generic template when a different third party is detected
THIRD_PARTY_ALERT_TEMPLATE = (
    "Your message mentions discussing case details with a third party "
    "({party}). Communications with non-parties may not be protected "
    "by solicitor-client privilege. Consider whether this information "
    "should be shared before proceeding."
)
