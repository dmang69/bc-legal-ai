"""Privilege layer — client-owned, query-enforced, production-gated."""

from backend.privilege.access_control import (
    AuthorizationContext,
    assert_document_readable,
    filter_documents_for_principal,
)
from backend.privilege.production_gate import ProductionDecision, run_production_gate
from backend.privilege.state_machine import InvalidPrivilegeTransition, transition_privilege
from backend.privilege.tagger import propose_privilege_tag

__all__ = [
    "AuthorizationContext",
    "InvalidPrivilegeTransition",
    "ProductionDecision",
    "assert_document_readable",
    "filter_documents_for_principal",
    "propose_privilege_tag",
    "run_production_gate",
    "transition_privilege",
]
