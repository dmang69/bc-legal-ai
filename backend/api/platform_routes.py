"""M1–M3 platform routes: auth, matters, evidence, citations, audit."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from backend.api.dependencies import (
    CurrentUser,
    RawBearerToken,
    require_matter_access,
    require_optional_matter_access,
)
from backend.api.rate_limit import (
    auth_login_rule,
    auth_register_rule,
    maybe_enforce_rate_limit,
)
from backend.api.session_cookies import clear_session_cookies, json_with_session
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
def register(request: Request, body: RegisterOrgBody) -> JSONResponse:
    # Per-IP limit (stops org-farming); email alone is weak because attackers rotate.
    maybe_enforce_rate_limit(request, auth_register_rule())
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
    # Body still includes token for API clients; HttpOnly cookie set for browsers.
    return json_with_session(session.to_dict(), token=session.token)


@router.post("/auth/login")
def login(request: Request, body: LoginBody) -> JSONResponse:
    # Per-IP and per-email sliding windows (credential stuffing / password spray).
    maybe_enforce_rate_limit(request, auth_login_rule())
    maybe_enforce_rate_limit(request, auth_login_rule(), extra_key=body.email.lower())
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
    return json_with_session(session.to_dict(), token=session.token)


@router.get("/auth/me")
def me(current_user: CurrentUser) -> dict[str, Any]:
    return current_user.to_dict()


@router.post("/auth/logout")
def logout(raw_token: RawBearerToken) -> JSONResponse:
    """Revoke session and clear HttpOnly cookies."""
    get_identity_service().revoke_session(raw_token)
    resp = JSONResponse(content={"status": "ok"})
    clear_session_cookies(resp)
    return resp


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


@router.post("/matters/{matter_id}/exports/{manifest_id}/package")
def build_export_package(
    matter_id: str,
    manifest_id: str,
    current_user: CurrentUser,
) -> Response:
    """ZIP court package (DOCX summary + manifest JSON). Requires APPROVED manifest."""
    try:
        reject_if_public_demo("court-ready export package")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    from backend.platform.court_export import build_court_package

    try:
        result = build_court_package(
            user=current_user, matter_id=matter_id, manifest_id=manifest_id
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    if not result.ok:
        raise HTTPException(
            status_code=400,
            detail={"error": result.error or "blocked", "blockers": result.blockers},
        )
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="export.package",
        org_id=current_user.org_id,
        matter_id=matter_id,
        resource_type="export_manifest",
        resource_id=manifest_id,
    )
    return Response(
        content=result.package_bytes,
        media_type=result.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "X-Court-Ready": "true",
        },
    )


class PdfExtractBody(BaseModel):
    """Base64 PDF bytes for native extract + optional OCR."""

    filename: str = "upload.pdf"
    content_base64: str = Field(min_length=1)
    force_ocr: bool = False


@router.post("/matters/{matter_id}/documents/pdf-extract")
def pdf_extract_route(
    matter_id: str,
    body: PdfExtractBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Extract text from PDF (pypdf); mark pages needing OCR; run OCR if available."""
    require_matter_access(current_user, matter_id, min_level="write")
    import base64

    try:
        raw = base64.b64decode(body.content_base64, validate=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {e}") from e
    from backend.platform.ocr import extract_with_ocr

    result = extract_with_ocr(raw, force_ocr=body.force_ocr)
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="document.pdf_extract",
        org_id=current_user.org_id,
        matter_id=matter_id,
        resource_type="document",
        resource_id=body.filename,
    )
    return {
        "matter_id": matter_id,
        "filename": body.filename,
        **result.to_dict(),
        "court_ready": False,
    }


class LawFetchBody(BaseModel):
    source_key: str = "RTA"
    url: str = ""
    persist: bool = True


@router.post("/knowledge/bc-laws/fetch")
def fetch_bc_laws_route(
    body: LawFetchBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Fetch official BC Laws HTML; never court_ready without human currency check."""
    try:
        reject_if_public_demo("live BC Laws network fetch")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    from knowledgebase.updater.bc_laws_fetcher import fetch_bc_laws

    result = fetch_bc_laws(
        body.source_key,
        url=body.url or None,
        persist=body.persist,
    )
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="knowledge.bc_laws_fetch",
        org_id=current_user.org_id,
        resource_type="knowledge_source",
        resource_id=body.source_key,
    )
    return result.to_dict()


@router.get("/knowledge/bc-laws/catalog")
def bc_laws_catalog(current_user: CurrentUser) -> dict[str, Any]:
    from knowledgebase.updater.bc_laws_fetcher import KNOWN_STATUTES

    return {
        "statutes": KNOWN_STATUTES,
        "statute_source": "BC Laws only",
        "court_ready": False,
        "note": "Fetch records currency line; human must re-verify before filing.",
    }


@router.get("/matters/{matter_id}/drafts/form-66")
def draft_form_66(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        return drafting_mod.petition_outline(current_user, matter_id)
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/matters/{matter_id}/drafts/form-66.docx")
def draft_form_66_docx(
    matter_id: str,
    current_user: CurrentUser,
) -> Response:
    """Download Form 66 petition scaffold as DOCX (never court-ready by itself)."""
    try:
        from backend.platform.form66 import form66_from_matter
        from backend.platform.matters import get_matter_store

        matter = get_matter_store().get_matter(current_user, matter_id)
        result = form66_from_matter(
            user=current_user,
            matter_id=matter_id,
            matter_title=str(matter.get("title") or ""),
            client_label=str(matter.get("client_label") or ""),
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    if not result.ok:
        raise HTTPException(status_code=500, detail=result.error or "Form 66 build failed")
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="draft.form66_docx",
        org_id=current_user.org_id,
        matter_id=matter_id,
        resource_type="draft",
        resource_id="form66",
    )
    return Response(
        content=result.docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "X-Court-Ready": "false",
            "X-Form-Number": "66",
        },
    )


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
    provider: str = ""
    model: str = ""
    temperature: Optional[float] = None


@router.get("/chat/capabilities")
def chat_capabilities() -> dict[str, Any]:
    return get_conversation_service().capabilities()


@router.get("/workspace/specialists")
def workspace_specialists() -> dict[str, Any]:
    return {"specialists": get_conversation_service().list_specialists()}


@router.get("/workspace/modes")
def workspace_modes() -> dict[str, Any]:
    return {"modes": get_conversation_service().list_modes()}


@router.get("/workspace/chat-types")
def workspace_chat_types() -> dict[str, Any]:
    return {"chat_types": get_conversation_service().list_chat_types()}


@router.get("/workspace/tools")
def workspace_tools() -> dict[str, Any]:
    return {"tools": get_conversation_service().list_tools()}


@router.get("/workspace/model-providers")
def workspace_model_providers() -> dict[str, Any]:
    return {"providers": get_conversation_service().list_model_providers()}


@router.get("/skills")
def list_skills_catalog() -> dict[str, Any]:
    """In-repo skill pack catalog (markdown operating procedures)."""
    return get_conversation_service().list_skills_catalog()


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
            provider=body.provider,
            model=body.model,
            temperature=body.temperature,
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


# ----- Enterprise AI suite (productivity, code, arena, web, providers) -----


class SummarizeBody(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)
    max_bullets: int = 8


class EmailDraftBody(BaseModel):
    purpose: str
    audience: str = "colleague"
    tone: str = "professional"
    points: list[str] = Field(default_factory=list)
    matter_label: str = ""


class CreativeBody(BaseModel):
    prompt: str
    style: str = "clear_prose"


class CodeAssistBody(BaseModel):
    code: str = ""
    language: str = ""
    mode: str = "complete"  # complete | debug | document
    error: str = ""
    intent: str = "continue"


class WebResearchBody(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    max_results: int = 5


class ArenaBody(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)
    providers: list[str] = Field(default_factory=list)
    mode: str = "balanced"


class ProviderCompleteBody(BaseModel):
    messages: list[dict[str, str]]
    system_prompt: str = ""
    provider: str = "safe_local"
    model: str = "safe-orchestrator"
    mode: str = "balanced"
    temperature: float = 0.2
    max_tokens: int = 2048


@router.get("/ai/suite")
def ai_suite_manifest(current_user: CurrentUser) -> dict[str, Any]:
    """Enterprise AI suite capability map (ChatGPT/Monica/Claude/Ollama/Copilot/Grok/Arena inspirations)."""
    from backend.platform.model_providers import get_model_provider_registry
    from backend.platform.web_research import web_research_enabled

    reg = get_model_provider_registry()
    return {
        "product": "BC Legal AI Associate — Enterprise AI Suite",
        "court_ready_default": False,
        "legal_advice": False,
        "inspirations": [
            "ChatGPT multi-turn chat",
            "Monica productivity tools",
            "Claude safety & reasoning",
            "Ollama local models",
            "Copilot code assist",
            "Grok live research (bounded)",
            "Arena model comparison",
        ],
        "endpoints": {
            "chat": "/v1/platform/conversations",
            "summarize": "/v1/platform/ai/summarize",
            "email": "/v1/platform/ai/email-draft",
            "creative": "/v1/platform/ai/creative",
            "code": "/v1/platform/ai/code",
            "web_research": "/v1/platform/ai/web-research",
            "arena": "/v1/platform/ai/arena",
            "complete": "/v1/platform/ai/complete",
            "providers": "/v1/platform/workspace/model-providers",
        },
        "providers": reg.list_providers(),
        "default_provider": reg.default_provider_id(),
        "web_research_enabled": web_research_enabled(),
        "external_llm_gated": True,
        "external_llm_enable_env": "ALA_ALLOW_EXTERNAL_LLM=1",
        "ollama_url_env": "ALA_OLLAMA_URL",
        "safety": [
            "harmlessness_gate",
            "honesty_disclaimers",
            "no_lawyer_impersonation",
            "court_ready_false",
            "matter_acl",
        ],
    }


@router.post("/ai/summarize")
def ai_summarize(body: SummarizeBody, current_user: CurrentUser) -> dict[str, Any]:
    from backend.platform.productivity_tools import summarize_text

    return summarize_text(body.text, max_bullets=body.max_bullets).to_dict()


@router.post("/ai/email-draft")
def ai_email(body: EmailDraftBody, current_user: CurrentUser) -> dict[str, Any]:
    from backend.platform.productivity_tools import draft_email

    return draft_email(
        purpose=body.purpose,
        audience=body.audience,
        tone=body.tone,
        points=body.points,
        matter_label=body.matter_label,
    ).to_dict()


@router.post("/ai/creative")
def ai_creative(body: CreativeBody, current_user: CurrentUser) -> dict[str, Any]:
    from backend.platform.productivity_tools import creative_writing

    return creative_writing(body.prompt, style=body.style).to_dict()


@router.post("/ai/code")
def ai_code(body: CodeAssistBody, current_user: CurrentUser) -> dict[str, Any]:
    from backend.platform.code_assistant import complete_code, debug_code, document_code

    if body.mode == "debug":
        return debug_code(body.code, body.error, language=body.language).to_dict()
    if body.mode == "document":
        return document_code(body.code, language=body.language).to_dict()
    return complete_code(body.code, language=body.language, intent=body.intent).to_dict()


@router.post("/ai/web-research")
def ai_web_research(body: WebResearchBody, current_user: CurrentUser) -> dict[str, Any]:
    from backend.platform.web_research import research

    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="ai.web_research",
        org_id=current_user.org_id,
        resource_type="research",
        resource_id=body.query[:80],
    )
    return research(body.query, max_results=body.max_results).to_dict()


@router.post("/ai/arena")
def ai_arena(body: ArenaBody, current_user: CurrentUser) -> dict[str, Any]:
    from backend.platform.arena import compare_models

    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="ai.arena",
        org_id=current_user.org_id,
        resource_type="arena",
    )
    return compare_models(body.prompt, providers=body.providers or None, mode=body.mode)


@router.post("/ai/complete")
def ai_complete(body: ProviderCompleteBody, current_user: CurrentUser) -> dict[str, Any]:
    """Direct multi-provider completion with safety post-process."""
    from backend.platform.ai_safety import enforce_output_safety
    from backend.platform.model_providers import ChatModelRequest, get_model_provider_registry
    from backend.platform import org_admin

    pid = body.provider or "safe_local"
    q = org_admin.check_quota(current_user, provider=pid)
    if not q.get("allowed"):
        raise HTTPException(status_code=429, detail=q.get("reason") or "quota denied")

    reg = get_model_provider_registry()
    resp = reg.complete(
        ChatModelRequest(
            messages=body.messages,
            system_prompt=body.system_prompt
            or (
                "Helpful, honest, harmless assistant. Not a lawyer. Not legal advice. "
                "court_ready remains false."
            ),
            model=body.model,
            mode=body.mode,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        ),
        provider_id=pid,
    )
    safe = enforce_output_safety(resp.content, mode=body.mode)
    usage = resp.usage or {}
    in_t = int(usage.get("prompt_tokens") or usage.get("input_tokens") or usage.get("prompt_eval_count") or 50)
    out_t = int(usage.get("completion_tokens") or usage.get("output_tokens") or usage.get("eval_count") or 100)
    tel = org_admin.record_usage(
        current_user,
        provider=resp.provider,
        model=resp.model,
        feature="complete",
        input_tokens=in_t,
        output_tokens=out_t,
    )
    return {
        "provider": resp.provider,
        "model": resp.model,
        "content": safe.rewritten_content or resp.content,
        "finish_reason": resp.finish_reason,
        "usage": resp.usage,
        "safety": safe.to_dict(),
        "telemetry": tel,
        "court_ready": False,
    }


class OrgSettingsBody(BaseModel):
    allowed_providers: Optional[list[str]] = None
    default_provider: Optional[str] = None
    daily_request_quota: Optional[int] = None
    monthly_token_budget: Optional[int] = None
    allow_external_llm: Optional[bool] = None
    allow_web_research: Optional[bool] = None


@router.get("/org/ai/settings")
def org_ai_settings(current_user: CurrentUser) -> dict[str, Any]:
    from backend.platform import org_admin

    return org_admin.get_settings(current_user.org_id).to_dict()


@router.put("/org/ai/settings")
def org_ai_settings_update(
    body: OrgSettingsBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    from backend.platform import org_admin

    try:
        settings = org_admin.update_settings(
            current_user,
            allowed_providers=body.allowed_providers,
            default_provider=body.default_provider,
            daily_request_quota=body.daily_request_quota,
            monthly_token_budget=body.monthly_token_budget,
            allow_external_llm=body.allow_external_llm,
            allow_web_research=body.allow_web_research,
        )
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="org.ai_settings_update",
        org_id=current_user.org_id,
        resource_type="org_ai_settings",
        resource_id=current_user.org_id,
    )
    return settings.to_dict()


@router.get("/org/ai/telemetry")
def org_ai_telemetry(current_user: CurrentUser) -> dict[str, Any]:
    from backend.platform import org_admin

    try:
        return org_admin.telemetry_summary(current_user)
    except AuthError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/org/ai/quota")
def org_ai_quota(current_user: CurrentUser, provider: str = "safe_local") -> dict[str, Any]:
    from backend.platform import org_admin

    return org_admin.check_quota(current_user, provider=provider)

