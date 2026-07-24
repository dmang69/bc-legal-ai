"""M1–M3 platform routes: auth, matters, evidence, citations, audit."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.api.dependencies import (
    CurrentUser,
    RawBearerToken,
    require_matter_access,
    require_optional_matter_access,
)
from backend.api.public_demo import (
    enforce_public_text,
    is_public_demo,
    public_deployment_safety,
    reject_if_public_demo,
)
from backend.audit import get_audit_ledger
from backend.db import get_db_backend, init_db
from backend.identity import AuthError, get_identity_service
from backend.platform.citations import list_citation_audit, list_knowledge_sources, verify_citation
from backend.platform.conflicts import get_conflict_service
from backend.platform.consent_store import get_consent_store
from backend.platform.conversation import get_conversation_service
from backend.platform import drafting as drafting_mod
from backend.platform.evidence import get_evidence_service
from backend.platform.export_manifest import (
    ExportApprovals,
    create_export_manifest,
    list_export_manifests,
)
from backend.platform.matters import get_matter_store
from backend.platform.workspace import (
    add_message as add_workspace_message,
    create_conversation as create_workspace_conversation_record,
    get_conversation as get_workspace_conversation_record,
    list_conversations as list_workspace_conversation_records,
)

router = APIRouter(prefix="/v1/platform", tags=["platform"])


class RegisterOrgBody(BaseModel):
    org_name: str
    email: str
    password: str
    display_name: str = ""


class LoginBody(BaseModel):
    email: str
    password: str


class MatterBody(BaseModel):
    title: str
    client_label: str = ""
    synthetic: bool = True


class ConflictBody(BaseModel):
    query_name: str
    matter_id: Optional[str] = None


class UploadMeta(BaseModel):
    filename: str
    content_type: str = "text/plain"
    text_content: str = ""
    synthetic: bool = True


class PropositionBody(BaseModel):
    text: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None
    classification: str = "UNCLASSIFIED"


class CitationBody(BaseModel):
    citation_text: str
    matter_id: str = ""
    expected_topic: str = ""


class ExportManifestBody(BaseModel):
    document_ids: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    destination: str = "export"
    human_confirmed_facts: bool = False
    citation_reviewed: bool = False
    privilege_reviewed: bool = False
    lawyer_approved: bool = False
    client_waiver_signed: bool = False


class WorkspaceAnalyzeBody(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    mode: str = "general"
    matter_id: str = ""


class WorkspaceConversationBody(BaseModel):
    matter_id: str = ""
    title: str = "Workspace conversation"
    mode: str = "general"


class WorkspaceMessageBody(BaseModel):
    author: str = "user"
    body: str = Field(min_length=1, max_length=8000)
    metadata: dict[str, Any] = Field(default_factory=dict)


_ALLOWED_WORKSPACE_MODES = {"general", "matter", "document", "research", "drafting", "agent"}


def _classify_legal_query(text: str, mode: str) -> dict[str, Any]:
    low = text.lower()
    issues: list[str] = []
    if any(term in low for term in ("judicial review", "jr", "patent unreasonable", "procedural fairness")):
        issues.append("judicial-review screening")
    if any(term in low for term in ("rta", "residential tenancy", "rtb", "tenancy")):
        issues.append("BC residential-tenancy context")
    if any(term in low for term in ("summarize", "summary", "explain")):
        issues.append("document-summary request")
    if any(term in low for term in ("deadline", "limitation", "days", "served")):
        issues.append("deadline-sensitive issue")
    if not issues:
        issues.append(f"{mode} legal triage")
    return {
        "issues": issues,
        "requires_human_review": True,
        "court_ready": False,
    }


@router.post("/workspace/analyze")
def workspace_analyze(body: WorkspaceAnalyzeBody) -> dict[str, Any]:
    mode = body.mode.strip().lower() or "general"
    if mode not in _ALLOWED_WORKSPACE_MODES:
        raise HTTPException(status_code=400, detail="Unsupported workspace mode")

    public_check = enforce_public_text(body.message)
    if not public_check.get("ok", False):
        raise HTTPException(status_code=403, detail=public_check)

    classification = _classify_legal_query(body.message, mode)
    citation_results: list[dict[str, Any]] = []
    citation_patterns = [
        r"\b(?:RTA|JRPA|ATA)\b(?:\s+s\.?\s*\d+[A-Za-z]?)?",
        r"\b(?:Residential Tenancy Act|Judicial Review Procedure Act|Administrative Tribunals Act)\b(?:\s+s\.?\s*\d+[A-Za-z]?)?",
    ]
    seen: set[str] = set()
    for pattern in citation_patterns:
        for match in re.finditer(pattern, body.message, flags=re.I):
            citation = match.group(0).strip()
            if citation.lower() in seen:
                continue
            seen.add(citation.lower())
            citation_results.append(
                verify_citation(
                    citation,
                    matter_id=body.matter_id,
                    expected_topic=" ".join(classification["issues"] + [body.message]),
                )
            )

    blockers = [
        "not legal advice",
        "human supervision required",
        "no court-ready output without verified sources and privilege review",
    ]
    if mode in {"research", "drafting"} and not citation_results:
        blockers.append("no verified citation pathway was detected in the request")
    if mode == "agent":
        blockers.append("agent execution requires explicit task approval before any external action")

    response_lines = [
        "I can triage this safely, but I cannot mark it court-ready.",
        f"Mode: {mode}.",
        "Detected: " + "; ".join(classification["issues"]) + ".",
        "Next safe step: provide source text, decision date/service details, and requested jurisdiction so evidence, deadline, citation, and privilege gates can run.",
    ]
    if citation_results:
        response_lines.append(
            "Citation check: "
            + "; ".join(f"{r['citation_text']} => {r['status']}" for r in citation_results)
            + "."
        )

    return {
        "message": "\n".join(response_lines),
        "mode": mode,
        "classification": classification,
        "citations": citation_results,
        "safety": {
            "court_ready": False,
            "legal_advice": False,
            "blockers": blockers,
        },
    }


@router.post("/workspace/conversations")
def create_workspace_conversation(
    body: WorkspaceConversationBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return create_workspace_conversation_record(
            user=current_user,
            matter_id=body.matter_id,
            title=body.title,
            mode=body.mode,
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/workspace/conversations")
def list_workspace_conversations(
    current_user: CurrentUser,
    matter_id: str = "",
) -> dict[str, Any]:
    try:
        return {"conversations": list_workspace_conversation_records(user=current_user, matter_id=matter_id)}
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/workspace/conversations/{conversation_id}")
def get_workspace_conversation(
    conversation_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return get_workspace_conversation_record(user=current_user, conversation_id=conversation_id)
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/workspace/conversations/{conversation_id}/messages")
def add_workspace_conversation_message(
    conversation_id: str,
    body: WorkspaceMessageBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return add_workspace_message(
            user=current_user,
            conversation_id=conversation_id,
            author=body.author,
            body=body.body,
            metadata=body.metadata,
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/status")
def platform_status() -> dict[str, Any]:
    backend = init_db()
    return {
        "db_backend": backend or get_db_backend(),
        "public_demo": is_public_demo(),
        "public_deployment": public_deployment_safety(),
        "modules": [
            "identity",
            "matters",
            "audit",
            "evidence",
            "citations",
            "citation_audit",
            "conflicts",
            "export_manifests",
            "workspace_persistence",
        ],
    }


@router.post("/auth/register")
def register(body: RegisterOrgBody) -> dict[str, Any]:
    try:
        reject_if_public_demo("user registration with persistence")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    idsvc = get_identity_service()
    try:
        org_id = idsvc.create_organization(body.org_name)
        user = idsvc.register_user(
            org_id=org_id,
            email=body.email,
            password=body.password,
            display_name=body.display_name or body.email,
            role="owner",
        )
        session = idsvc.login(email=body.email, password=body.password)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    get_audit_ledger().append(
        actor_id=user.user_id,
        action="auth.register",
        org_id=org_id,
        resource_type="user",
        resource_id=user.user_id,
    )
    return session.to_dict()


@router.post("/auth/login")
def login(body: LoginBody) -> dict[str, Any]:
    try:
        session = get_identity_service().login(email=body.email, password=body.password)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    get_audit_ledger().append(
        actor_id=session.user.user_id,
        action="auth.login",
        org_id=session.user.org_id,
        resource_type="session",
        resource_id=session.session_id,
    )
    return session.to_dict()


@router.get("/auth/me")
def me(current_user: CurrentUser) -> dict[str, Any]:
    return current_user.to_dict()


@router.post("/auth/logout")
def logout(raw_token: RawBearerToken) -> dict[str, str]:
    """Revoke the current session by invalidating its bearer token."""
    get_identity_service().revoke_session(raw_token)
    return {"status": "ok"}


@router.post("/matters")
def create_matter(
    body: MatterBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    if not body.synthetic:
        try:
            reject_if_public_demo("non-synthetic matter creation")
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e)) from e
    return get_matter_store().create_matter(
        user=current_user,
        title=body.title,
        client_label=body.client_label,
        synthetic=body.synthetic,
    )


@router.get("/matters")
def list_matters(current_user: CurrentUser) -> dict[str, Any]:
    return {"matters": get_matter_store().list_matters(current_user)}


@router.get("/matters/{matter_id}")
def get_matter(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return get_matter_store().get_matter(current_user, matter_id)
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/conflicts/check")
def conflict_check(
    body: ConflictBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    return get_conflict_service().check_name(
        user=current_user, query_name=body.query_name, matter_id=body.matter_id
    )


@router.post("/matters/{matter_id}/documents/text")
def upload_text_document(
    matter_id: str,
    body: UploadMeta,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        reject_if_public_demo("document upload")
    except PermissionError:
        if not body.synthetic:
            raise HTTPException(status_code=403, detail="Public demo rejects uploads")
    data = body.text_content.encode("utf-8")
    try:
        return get_evidence_service().quarantine_upload(
            user=current_user,
            matter_id=matter_id,
            filename=body.filename,
            data=data,
            content_type=body.content_type,
            synthetic=body.synthetic,
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/matters/{matter_id}/documents")
def list_documents(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return {"documents": get_evidence_service().list_documents(current_user, matter_id)}
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/matters/{matter_id}/propositions")
def add_proposition(
    matter_id: str,
    body: PropositionBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return get_evidence_service().add_proposition(
            user=current_user,
            matter_id=matter_id,
            text=body.text,
            document_id=body.document_id,
            page_id=body.page_id,
            classification=body.classification,
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/citations/verify")
def citations_verify(
    body: CitationBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Verify a citation. Requires authentication and matter authorization."""
    matter_id = require_optional_matter_access(current_user, body.matter_id)
    result = verify_citation(
        body.citation_text,
        matter_id=matter_id,
        expected_topic=body.expected_topic,
    )
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="citation.verify",
        org_id=current_user.org_id,
        matter_id=matter_id,
        resource_type="citation",
        detail={"citation_text": body.citation_text, "status": result.get("status")},
    )
    return result


@router.get("/knowledge/sources")
def knowledge_sources(
    current_user: CurrentUser,
) -> dict[str, Any]:
    """List knowledge sources. Requires authentication."""
    return {"sources": list_knowledge_sources()}


@router.get("/citations/audit")
def citations_audit(
    current_user: CurrentUser,
    matter_id: str = "",
) -> dict[str, Any]:
    """Get citation audit history. Requires authentication and matter authorization."""
    matter_id = require_optional_matter_access(current_user, matter_id)
    return {"matter_id": matter_id, "citations": list_citation_audit(matter_id)}


@router.get("/audit/verify")
def audit_verify(current_user: CurrentUser) -> dict[str, Any]:
    # Auth check: only authenticated users may verify the audit chain
    return get_audit_ledger().verify_chain()


class DeadlineBody(BaseModel):
    matter_id: str
    label: str = "deadline"
    start_date: Optional[str] = None
    service_method: Optional[str] = None
    window_days: Optional[int] = None
    synthetic: bool = True
    statutory_basis: str = ""


@router.post("/deadlines/calculate")
def platform_deadline(
    body: DeadlineBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Calculate a provisional deadline. Requires authentication and matter authorization.
    human_confirmed cannot be supplied by the caller — must be a separate authenticated approval event."""
    from backend.platform.deadlines_engine import calculate_matter_deadline

    matter_id = require_matter_access(current_user, body.matter_id)

    # human_confirmed is always False from API — must be approved via separate endpoint
    result = calculate_matter_deadline(
        matter_id=matter_id,
        label=body.label,
        start_date=body.start_date,
        service_method=body.service_method,
        window_days=body.window_days,
        human_confirmed=False,
        synthetic=body.synthetic,
        statutory_basis=body.statutory_basis,
    )
    # Write audit event
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="deadline.calculate",
        org_id=current_user.org_id,
        matter_id=matter_id,
        resource_type="deadline",
        detail={"label": body.label, "state": result.get("state", "")},
    )
    return result


class ConsentBody(BaseModel):
    subject_id: str
    category: str = "AI_ANALYSIS"
    purpose: str
    notice_version: str = "privacy-notice-3.1"
    model_scope: str = "PRIVATE_INFERENCE_ONLY"


@router.post("/matters/{matter_id}/consents")
def grant_consent(
    matter_id: str,
    body: ConsentBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return get_consent_store().grant(
            user=current_user,
            matter_id=matter_id,
            subject_id=body.subject_id,
            category=body.category,
            purpose=body.purpose,
            notice_version=body.notice_version,
            model_scope=body.model_scope,
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/matters/{matter_id}/consents")
def list_consents(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return {"consents": get_consent_store().list_for_matter(current_user, matter_id)}
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/consents/{consent_id}/withdraw")
def withdraw_consent(
    consent_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return get_consent_store().withdraw(user=current_user, consent_id=consent_id)
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/matters/{matter_id}/consents/evaluate-ai")
def evaluate_ai_consent(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    # Auth check: user must be authenticated to evaluate consent state
    return get_consent_store().evaluate_optional_ai(matter_id)


@router.post("/matters/{matter_id}/exports/manifest")
def create_manifest(
    matter_id: str,
    body: ExportManifestBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return create_export_manifest(
            user=current_user,
            matter_id=matter_id,
            document_ids=body.document_ids,
            citation_ids=body.citation_ids,
            destination=body.destination,
            approvals=ExportApprovals(
                human_confirmed_facts=body.human_confirmed_facts,
                citation_reviewed=body.citation_reviewed,
                privilege_reviewed=body.privilege_reviewed,
                lawyer_approved=body.lawyer_approved,
                client_waiver_signed=body.client_waiver_signed,
            ),
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/matters/{matter_id}/exports/manifest")
def list_manifests(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return {"manifests": list_export_manifests(current_user, matter_id)}
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/matters/{matter_id}/drafts/form-66")
def draft_form_66(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return drafting_mod.petition_outline(current_user, matter_id)
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/matters/{matter_id}/drafts/form-67")
def draft_form_67(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return drafting_mod.response_outline(current_user, matter_id)
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


# ----- Conversational workspace -----


class ConversationCreate(BaseModel):
    title: str = "New chat"
    chat_type: str = "general"
    matter_id: Optional[str] = None
    model_mode: str = "balanced"
    specialist: str = "bc_legal_associate"


class ChatSendBody(BaseModel):
    content: str
    attachments: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/workspace/specialists")
def workspace_specialists() -> dict[str, Any]:
    return {"specialists": get_conversation_service().list_specialists()}


@router.get("/workspace/modes")
def workspace_modes() -> dict[str, Any]:
    return {"modes": get_conversation_service().list_modes()}


@router.post("/conversations")
def create_conversation(
    body: ConversationCreate,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return get_conversation_service().create(
            user=current_user,
            title=body.title,
            chat_type=body.chat_type,
            matter_id=body.matter_id,
            model_mode=body.model_mode,
            specialist=body.specialist,
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/conversations")
def list_conversations(
    current_user: CurrentUser,
) -> dict[str, Any]:
    return {"conversations": get_conversation_service().list_for_user(current_user)}


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        conv = get_conversation_service().get(current_user, conversation_id)
        msgs = get_conversation_service().list_messages(current_user, conversation_id)
        return {"conversation": conv, "messages": msgs}
    except AuthError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/conversations/{conversation_id}/messages")
def send_message(
    conversation_id: str,
    body: ChatSendBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return get_conversation_service().send(
            user=current_user,
            conversation_id=conversation_id,
            content=body.content,
            attachments=body.attachments,
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/conversations/{conversation_id}/messages/stream")
def send_message_stream(
    conversation_id: str,
    body: ChatSendBody,
    current_user: CurrentUser,
) -> StreamingResponse:
    """SSE-style text stream (scaffold)."""
    def gen():
        try:
            for chunk in get_conversation_service().stream_tokens(
                current_user, conversation_id, body.content
            ):
                yield f"data: {json.dumps({'t': chunk})}\n\n"
            yield 'data: {"done": true}\n\n'
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")

