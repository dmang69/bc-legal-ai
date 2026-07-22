"""
Privilege boundary enforcement hooks (API middleware skeleton).

Wraps request paths that touch evidence, chat, export, or production.
Fail-closed: PROTECTED/RESTRICTED material requires explicit gate clearance.

Integrates with backend.privilege.production_gate and services.compliance.
Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from architecture.evidence_node import PrivilegeClass
from services.compliance.privilege_ops_log import PrivilegeOpLog


class GuardAction(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REQUIRE_HITL = "REQUIRE_HITL"
    REQUIRE_PRODUCTION_GATE = "REQUIRE_PRODUCTION_GATE"


SENSITIVE_OPS = frozenset(
    {
        "export",
        "produce_to_opposing",
        "file_with_court",
        "send_external",
        "chat_with_third_party",
        "copy_to_clipboard",
        "download_original",
    }
)


@dataclass
class GuardContext:
    matter_id: str
    actor_id: str
    operation: str
    privilege_class: PrivilegeClass = PrivilegeClass.OPEN
    production_gate_cleared: bool = False
    lawyer_confirmed: bool = False
    client_waiver: bool = False


@dataclass
class GuardResult:
    action: GuardAction
    allowed: bool
    reason: str
    log_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "allowed": self.allowed,
            "reason": self.reason,
            "log_id": self.log_id,
        }


@dataclass
class PrivilegeGuard:
    log: PrivilegeOpLog = field(default_factory=PrivilegeOpLog)

    def check(self, ctx: GuardContext) -> GuardResult:
        op = (ctx.operation or "").lower().strip()
        pc = ctx.privilege_class

        if pc == PrivilegeClass.OPEN:
            entry = self.log.record(
                matter_id=ctx.matter_id,
                operation=op,
                actor_id=ctx.actor_id,
                privilege_class=pc.value,
                blocked=False,
            )
            return GuardResult(
                action=GuardAction.ALLOW,
                allowed=True,
                reason="OPEN privilege class",
                log_id=entry["id"],
            )

        if op in SENSITIVE_OPS and pc in (
            PrivilegeClass.PROTECTED,
            PrivilegeClass.RESTRICTED,
        ):
            if not ctx.production_gate_cleared:
                entry = self.log.record(
                    matter_id=ctx.matter_id,
                    operation=op,
                    actor_id=ctx.actor_id,
                    privilege_class=pc.value,
                    blocked=True,
                    detail={"need": "production_gate"},
                )
                return GuardResult(
                    action=GuardAction.REQUIRE_PRODUCTION_GATE,
                    allowed=False,
                    reason="Protected/restricted material requires production gate clearance.",
                    log_id=entry["id"],
                )
            if not ctx.lawyer_confirmed:
                entry = self.log.record(
                    matter_id=ctx.matter_id,
                    operation=op,
                    actor_id=ctx.actor_id,
                    privilege_class=pc.value,
                    blocked=True,
                    detail={"need": "lawyer_confirm"},
                )
                return GuardResult(
                    action=GuardAction.REQUIRE_HITL,
                    allowed=False,
                    reason="Lawyer two-factor confirmation required before privileged export.",
                    log_id=entry["id"],
                )

        entry = self.log.record(
            matter_id=ctx.matter_id,
            operation=op,
            actor_id=ctx.actor_id,
            privilege_class=pc.value,
            blocked=False,
        )
        return GuardResult(
            action=GuardAction.ALLOW,
            allowed=True,
            reason="Privilege checks passed",
            log_id=entry["id"],
        )


def privilege_guard_middleware(
    guard: PrivilegeGuard,
) -> Callable[[GuardContext], GuardResult]:
    """Factory for ASGI/FastAPI dependency-style wrapper."""

    def _run(ctx: GuardContext) -> GuardResult:
        return guard.check(ctx)

    return _run
