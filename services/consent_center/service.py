"""
Consent Management Center (Layer 5) — current state, modify/withdraw, history, plain language.

Wraps HITL consent ledger for client-facing UX.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.reasoning.hitl.consent.ledger import ConsentLedger
from services.reasoning.hitl.consent.scopes import ConsentScope, plain_language_for


@dataclass
class ConsentCenter:
    ledger: ConsentLedger = field(default_factory=ConsentLedger)

    def current_state(self, matter_id: str) -> dict[str, Any]:
        state = self.ledger.current_state(matter_id)
        # unique category values only
        cats = sorted({s.value for s in ConsentScope})
        state["explanations"] = {c: plain_language_for(c) for c in cats}
        return state

    def grant(
        self,
        *,
        matter_id: str,
        client_id: str,
        scope: str,
    ) -> dict[str, Any]:
        rec = self.ledger.grant(
            matter_id=matter_id,
            client_id=client_id,
            scope=scope,
        )
        return rec.to_dict()

    def withdraw(
        self,
        *,
        matter_id: str,
        scope: str,
        reason: str = "client_request",
    ) -> list[dict[str, Any]]:
        withdrawn = self.ledger.withdraw_scope(
            matter_id=matter_id, scope=scope, reason=reason
        )
        return [w.to_dict() for w in withdrawn]

    def history(self, matter_id: str) -> dict[str, Any]:
        return {
            "records": self.ledger.history(matter_id),
            "audit": [e.to_dict() for e in self.ledger.audit.for_matter(matter_id)],
        }

    def plain_language(self, scope: str) -> str:
        return plain_language_for(scope)
