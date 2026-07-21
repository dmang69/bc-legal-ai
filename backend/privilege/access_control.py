"""
Zero-trust privilege boundary — enforced at the filter/query layer.

Opposing counsel and tribunal principals never receive direct document access.
AI associate sees only task-scoped rows in AI_VISIBLE_PRIVILEGE states.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from architecture.privilege_schemas import (
    AI_VISIBLE_PRIVILEGE,
    MatterAccessGrant,
    PrincipalRole,
    PrivilegeMetadata,
    PrivilegeStatus,
)


@dataclass
class DocumentView:
    document_id: str
    matter_id: str
    privilege: PrivilegeMetadata
    storage_prefix: str = "non_privileged"


@dataclass
class AuthorizationContext:
    user_id: str
    role: PrincipalRole
    grants: list[MatterAccessGrant]
    active_task_id: Optional[str] = None


class PrivilegeAccessDenied(PermissionError):
    pass


def _grant_for(ctx: AuthorizationContext, matter_id: str) -> MatterAccessGrant | None:
    for g in ctx.grants:
        if not g.active or g.matter_id != matter_id or g.user_id != ctx.user_id:
            continue
        if g.role != ctx.role:
            continue
        if ctx.role == PrincipalRole.AI_ASSOCIATE:
            if not ctx.active_task_id or g.task_id != ctx.active_task_id:
                continue
        return g
    return None


def filter_documents_for_principal(
    docs: Iterable[DocumentView],
    ctx: AuthorizationContext,
) -> list[DocumentView]:
    """Query-layer filter. Never return opposing counsel / tribunal direct access."""
    if ctx.role in (PrincipalRole.OPPOSING_COUNSEL, PrincipalRole.TRIBUNAL_COURT):
        return []

    out: list[DocumentView] = []
    for doc in docs:
        grant = _grant_for(ctx, doc.matter_id)
        if grant is None:
            continue

        status = doc.privilege.privilege_status

        if ctx.role == PrincipalRole.AI_ASSOCIATE:
            # AI never sees WAIVED material as a free dump; only task-scoped protected set
            if status not in AI_VISIBLE_PRIVILEGE:
                continue
            if not doc.privilege.human_confirmed and status != PrivilegeStatus.UNCLAIMED:
                # Prefer confirmed tags for AI consumption of claimed material
                if status in AI_VISIBLE_PRIVILEGE and not doc.privilege.human_confirmed:
                    continue
            out.append(doc)
            continue

        # Human roles: full matter access per grant, including UNCLAIMED for review
        if status == PrivilegeStatus.WAIVED and ctx.role == PrincipalRole.PARALEGAL:
            # Paralegals: waived material still matter-scoped but often production-sensitive
            pass
        out.append(doc)

    return out


def assert_document_readable(doc: DocumentView, ctx: AuthorizationContext) -> None:
    allowed = filter_documents_for_principal([doc], ctx)
    if not allowed:
        raise PrivilegeAccessDenied(
            f"Access denied for user={ctx.user_id} role={ctx.role.value} "
            f"doc={doc.document_id} matter={doc.matter_id}"
        )


def storage_key_prefix(
    firm_id: str,
    matter_id: str,
    *,
    privileged: bool,
) -> str:
    """Logical segregation path (KMS binding is infrastructure Phase 2)."""
    branch = "privileged" if privileged else "non_privileged"
    return f"tenant/{firm_id}/matter/{matter_id}/{branch}"
