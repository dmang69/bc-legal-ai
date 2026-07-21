"""Privilege status transitions — client-owned metadata only."""

from __future__ import annotations

from architecture.privilege_schemas import (
    PRIVILEGE_TRANSITIONS,
    PrivilegeMetadata,
    PrivilegeStatus,
    WaiverEvent,
    _utcnow,
)


class InvalidPrivilegeTransition(ValueError):
    pass


def transition_privilege(
    meta: PrivilegeMetadata,
    new_status: PrivilegeStatus,
    *,
    actor_id: str,
    reason: str,
    proceeding_id: str | None = None,
    waiver: WaiverEvent | None = None,
) -> PrivilegeMetadata:
    allowed = PRIVILEGE_TRANSITIONS.get(meta.privilege_status, frozenset())
    if new_status not in allowed:
        raise InvalidPrivilegeTransition(
            f"Cannot transition {meta.privilege_status.value} → {new_status.value}"
        )

    if new_status == PrivilegeStatus.WAIVED:
        if waiver is None:
            raise InvalidPrivilegeTransition(
                "WAIVED requires a WaiverEvent and client-side authorization workflow"
            )
        meta.waiver_events.append(waiver)

    if new_status == PrivilegeStatus.CLAIMED and meta.claim_date is None:
        meta.claim_date = _utcnow()

    if new_status == PrivilegeStatus.ASSERTED:
        meta.asserted_in = proceeding_id or meta.asserted_in
        if not meta.asserted_in:
            raise InvalidPrivilegeTransition("ASSERTED requires asserted_in proceeding_id")

    meta.privilege_status = new_status
    # reason/actor recorded by audit layer at call site
    _ = (actor_id, reason)
    return meta
