"""Privilege layer — client-owned, query-enforced, production-gated."""

from backend.privilege.access_control import (
    AuthorizationContext,
    assert_document_readable,
    filter_documents_for_principal,
)
from backend.privilege.chat_guard import guard_user_message, scan_message_for_privilege_risk
from backend.privilege.production_gate import ProductionDecision, run_production_gate
from backend.privilege.state_machine import InvalidPrivilegeTransition, transition_privilege
from backend.privilege.tagger import propose_privilege_tag

__all__ = [
    "AuthorizationContext",
    "InvalidPrivilegeTransition",
    "ProductionDecision",
    "assert_document_readable",
    "filter_documents_for_principal",
    "guard_user_message",
    "propose_privilege_tag",
    "run_production_gate",
    "scan_message_for_privilege_risk",
    "transition_privilege",
]
