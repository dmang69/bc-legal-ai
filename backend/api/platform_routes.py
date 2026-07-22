"""M1–M3 platform routes: auth, matters, evidence, citations, audit."""

from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.api.public_demo import is_public_demo, reject_if_public_demo
from backend.audit import get_audit_ledger
from backend.db import get_db_backend, init_db
from backend.identity import AuthError, get_identity_service
from backend.platform.citations import list_knowledge_sources, verify_citation
from backend.platform.conflicts import get_conflict_service
from backend.platform.consent_store import get_consent_store
from backend.platform import drafting as drafting_mod
from backend.platform.evidence import get_evidence_service
from backend.platform.conversation import get_conversation_service
from backend.platform.matters import get_matter_store

router = APIRouter(prefix="/v1/platform", tags=["platform"])


def _user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.split(" ", 1)[1].strip()
    try:
        return get_identity_service().resolve_token(token)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


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


@router.get("/status")
def platform_status() -> dict[str, Any]:
    backend = init_db()
    return {
        "db_backend": backend or get_db_backend(),
        "public_demo": is_public_demo(),
        "modules": ["identity", "matters", "audit", "evidence", "citations", "conflicts"],
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
def me(authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
    return _user(authorization).to_dict()


@router.post("/auth/logout")
def logout(authorization: Optional[str] = Header(default=None)) -> dict[str, str]:
    if authorization and authorization.lower().startswith("bearer "):
        get_identity_service().revoke_session(authorization.split(" ", 1)[1].strip())
    return {"status": "ok"}


@router.post("/matters")
def create_matter(
    body: MatterBody, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    user = _user(authorization)
    if not body.synthetic:
        try:
            reject_if_public_demo("non-synthetic matter creation")
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e)) from e
    return get_matter_store().create_matter(
        user=user,
        title=body.title,
        client_label=body.client_label,
        synthetic=body.synthetic,
    )


@router.get("/matters")
def list_matters(authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
    user = _user(authorization)
    return {"matters": get_matter_store().list_matters(user)}


@router.get("/matters/{matter_id}")
def get_matter(
    matter_id: str, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        return get_matter_store().get_matter(user, matter_id)
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/conflicts/check")
def conflict_check(
    body: ConflictBody, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    user = _user(authorization)
    return get_conflict_service().check_name(
        user=user, query_name=body.query_name, matter_id=body.matter_id
    )


@router.post("/matters/{matter_id}/documents/text")
def upload_text_document(
    matter_id: str,
    body: UploadMeta,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        reject_if_public_demo("document upload")
    except PermissionError:
        if not body.synthetic:
            raise HTTPException(status_code=403, detail="Public demo rejects uploads")
    data = body.text_content.encode("utf-8")
    try:
        return get_evidence_service().quarantine_upload(
            user=user,
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
    matter_id: str, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        return {"documents": get_evidence_service().list_documents(user, matter_id)}
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/matters/{matter_id}/propositions")
def add_proposition(
    matter_id: str,
    body: PropositionBody,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        return get_evidence_service().add_proposition(
            user=user,
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
def citations_verify(body: CitationBody) -> dict[str, Any]:
    return verify_citation(
        body.citation_text,
        matter_id=body.matter_id,
        expected_topic=body.expected_topic,
    )


@router.get("/knowledge/sources")
def knowledge_sources() -> dict[str, Any]:
    return {"sources": list_knowledge_sources()}


@router.get("/audit/verify")
def audit_verify(authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
    _user(authorization)
    return get_audit_ledger().verify_chain()


class DeadlineBody(BaseModel):
    matter_id: str
    label: str = "deadline"
    start_date: Optional[str] = None
    service_method: Optional[str] = None
    window_days: Optional[int] = None
    human_confirmed: bool = False
    synthetic: bool = True
    statutory_basis: str = ""


@router.post("/deadlines/calculate")
def platform_deadline(body: DeadlineBody) -> dict[str, Any]:
    from backend.platform.deadlines_engine import calculate_matter_deadline

    return calculate_matter_deadline(
        matter_id=body.matter_id,
        label=body.label,
        start_date=body.start_date,
        service_method=body.service_method,
        window_days=body.window_days,
        human_confirmed=body.human_confirmed,
        synthetic=body.synthetic,
        statutory_basis=body.statutory_basis,
    )


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
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        return get_consent_store().grant(
            user=user,
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
    matter_id: str, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        return {"consents": get_consent_store().list_for_matter(user, matter_id)}
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/consents/{consent_id}/withdraw")
def withdraw_consent(
    consent_id: str, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        return get_consent_store().withdraw(user=user, consent_id=consent_id)
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/matters/{matter_id}/consents/evaluate-ai")
def evaluate_ai_consent(
    matter_id: str, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    _user(authorization)
    return get_consent_store().evaluate_optional_ai(matter_id)


@router.get("/matters/{matter_id}/drafts/form-66")
def draft_form_66(
    matter_id: str, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        return drafting_mod.petition_outline(user, matter_id)
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/matters/{matter_id}/drafts/form-67")
def draft_form_67(
    matter_id: str, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        return drafting_mod.response_outline(user, matter_id)
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
    body: ConversationCreate, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        return get_conversation_service().create(
            user=user,
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
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = _user(authorization)
    return {"conversations": get_conversation_service().list_for_user(user)}


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str, authorization: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        conv = get_conversation_service().get(user, conversation_id)
        msgs = get_conversation_service().list_messages(user, conversation_id)
        return {"conversation": conv, "messages": msgs}
    except AuthError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/conversations/{conversation_id}/messages")
def send_message(
    conversation_id: str,
    body: ChatSendBody,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = _user(authorization)
    try:
        return get_conversation_service().send(
            user=user,
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
    authorization: Optional[str] = Header(default=None),
):
    """SSE-style text stream (scaffold)."""
    user = _user(authorization)

    def gen():
        try:
            for chunk in get_conversation_service().stream_tokens(
                user, conversation_id, body.content
            ):
                yield f"data: {json.dumps({'t': chunk})}\n\n"
            yield 'data: {"done": true}\n\n'
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
