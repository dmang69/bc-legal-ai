"""Citation Clerk — authority gate (no network calls yet)."""

from __future__ import annotations

from architecture.schemas import AuthorityRecord, AuthorityStatus, court_ready_allowed


def gate_summary(authorities: list[AuthorityRecord]) -> dict:
    allowed, blockers = court_ready_allowed(authorities)
    counts = {s.value: 0 for s in AuthorityStatus}
    for a in authorities:
        counts[a.status.value] += 1
    return {
        "court_ready_allowed": allowed,
        "blockers": blockers,
        "counts": counts,
    }


def assert_court_ready(authorities: list[AuthorityRecord]) -> None:
    allowed, blockers = court_ready_allowed(authorities)
    if not allowed:
        raise PermissionError(
            "Court-ready mode blocked. Resolve UNVERIFIED/REJECTED authorities:\n"
            + "\n".join(f"  - {b}" for b in blockers)
        )
