"""
BC Legal AI Associate — modular monolith API gateway.

Run (dev):
  pip install fastapi uvicorn
  uvicorn backend.api.main:app --reload --port 8000

M1 platform (auth, matters, audit, evidence) uses SQLite by default
or Postgres when ALA_POSTGRES_URL is set. HITL/post-resolution remain
process-local until migrated.

Not legal advice. Do not expose to the public internet with client data.
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.api.dependencies import CurrentUser, require_matter_access
from backend.api.platform_routes import router as platform_router
from backend.api.public_demo import (
    assert_public_deployment_safe,
    enforce_public_text,
    is_public_demo,
    public_deployment_safety,
    reject_if_public_demo,
)
from backend.api.state import hitl, post_resolution
from backend.audit import get_audit_ledger
from backend.db import get_db_backend, init_db
from services.deadlines.jr_clock import JrClockRequest, calculate_jr_clock
from services.deadlines.states import calculate_deadline
from services.post_resolution.enforcement.packages import PackageType
from services.reasoning.hitl.exceptions.kinds import ExceptionKind, Severity
from services.reasoning.hitl.privilege_check.production import OutputClass
from services.reasoning.hitl.schemas.common import ModelDestination


@asynccontextmanager
async def lifespan(_app: FastAPI):
    assert_public_deployment_safe()
    init_db()
    yield





def _client_dir() -> Path:
    if getattr(sys, "frozen", False):
        # PyInstaller bundle
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        cand = base / "frontend" / "client"
        if cand.is_dir():
            return cand
        return Path(sys.executable).resolve().parent / "frontend" / "client"
    return Path(__file__).resolve().parents[2] / "frontend" / "client"


app = FastAPI(
    title="BC Legal AI Associate — Platform API",
    version="0.4.0",
    description=(
        "Modular monolith: identity, matters, audit, evidence, HITL, post-resolution. "
        "Not a lawyer. Not legal advice."
    ),
    lifespan=lifespan,
)

def _cors_origins() -> list[str]:
    """Environment-specific CORS allowlist. Fail on wildcard outside dev."""
    mode = os.environ.get("APP_MODE", "development").strip().lower()
    if mode == "development":
        return ["*"]  # Allow all for local development only
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    # Safe default for non-dev: no external origins
    return ["http://localhost:8000", "http://127.0.0.1:8000"]


_cors = _cors_origins()
_mode = os.environ.get("APP_MODE", "development").strip().lower()
if len(_cors) == 1 and _cors[0] == "*" and _mode != "development":
    raise RuntimeError(
        "Wildcard CORS (*) is forbidden outside APP_MODE=development. "
        "Set CORS_ORIGINS environment variable to a comma-separated allowlist."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Requested-With"],
    expose_headers=["Content-Disposition", "X-Request-Id"],
)

app.include_router(platform_router)

_CLIENT = _client_dir()
if _CLIENT.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_CLIENT)), name="assets")


@app.get("/")
def root_ui():
    index = _CLIENT / "index.html"
    if index.is_file():
        return FileResponse(index)
    return RedirectResponse(url="/docs")


@app.get("/index.html")
def index_html():
    return FileResponse(_CLIENT / "index.html")


@app.get("/styles.css")
def styles_css():
    return FileResponse(_CLIENT / "styles.css")


@app.get("/app.js")
def app_js():
    return FileResponse(_CLIENT / "app.js")


@app.get("/sw.js")
def service_worker():
    return FileResponse(_CLIENT / "sw.js")


@app.get("/manifest.webmanifest")
def web_manifest():
    return FileResponse(
        _CLIENT / "manifest.webmanifest",
        media_type="application/manifest+json",
    )


@app.get("/icons/{name}")
def icons(name: str):
    path = _CLIENT / "icons" / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="icon not found")
    return FileResponse(path)


@app.get("/health")
def health() -> dict[str, Any]:
    """Legacy health endpoint — returns status based on deployment safety."""
    try:
        db = get_db_backend()
    except Exception:
        db = "unknown"
    safety = public_deployment_safety()
    return {
        "status": "ok" if safety["safe"] else "unsafe",
        "phase": "m1-platform",
        "mode": "public_demo" if is_public_demo() else "platform",
        "platform": "api+static-client",
        "app_mode": safety["app_mode"],
        "db_backend": db,
        "public_deployment": safety,
    }


@app.get("/health/live")
def health_live() -> dict[str, Any]:
    """Liveness probe: process is alive."""
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready() -> dict[str, Any]:
    """Readiness probe: checks database and other dependencies."""
    issues: list[str] = []
    try:
        db = get_db_backend()
        if db == "unknown":
            issues.append("database_backend_unknown")
    except Exception as e:
        issues.append(f"database_unreachable: {e}")
        db = "error"

    safety = public_deployment_safety()
    if not safety["safe"]:
        for v in safety.get("violations", []):
            issues.append(f"deployment_violation: {v}")

    healthy = len(issues) == 0
    return {
        "status": "ok" if healthy else "unhealthy",
        "db_backend": db,
        "issues": issues,
        "public_demo": is_public_demo(),
    }


@app.get("/v1/design-locks")
def design_locks() -> dict[str, Any]:
    return {
        "consent_is_not_privilege": True,
        "withdrawal_is_not_unconditional_delete": True,
        "petition_form": "Form 66",
        "response_to_petition_form": "Form 67",
        "interlocutory_form": "Form 32",
        "jr_default_window": "60 days from issuance of final decision",
        "ata_s57_2": "extension pathway — counsel only, not auto-granted",
        "messaging": "MODEL_B_WORKSPACE default — not E2EE + server AI",
        "rtb_archive": "PARTIAL — absence is not non-existence",
        "statute_source": "BC Laws only",
    }


# ----- Phase 3 HITL: consent -----


class ConsentGrantBody(BaseModel):
    subject_id: str
    category: str
    purpose: str = ""
    notice_version: str = "privacy-notice-3.1"
    model_scope: str = "PRIVATE_INFERENCE_ONLY"


class EvaluateBody(BaseModel):
    matter_id: str
    subject_id: str
    data_categories: list[str]
    purpose: str
    model_destination: str = "PRIVATE_INFERENCE_ONLY"


@app.post("/v1/matters/{matter_id}/consents")
def grant_consent(
    matter_id: str,
    body: ConsentGrantBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        rec = hitl.consents.grant(
            matter_id=matter_id,
            client_id=body.subject_id,
            subject_id=body.subject_id,
            scope=body.category,
            purpose=body.purpose,
            notice_version=body.notice_version,
            model_scope=body.model_scope,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="consent.grant",
        org_id=current_user.org_id,
        matter_id=matter_id,
        resource_type="consent",
    )
    return rec.to_dict()


@app.get("/v1/matters/{matter_id}/consents")
def list_consents(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    return {
        "matter_id": matter_id,
        "state": hitl.consents.current_state(matter_id),
        "records": hitl.consents.history(matter_id),
    }


@app.post("/v1/consents/{consent_id}/withdraw")
def withdraw_consent(
    consent_id: str,
    current_user: CurrentUser,
    reason: str = "client_withdrawal",
) -> dict[str, Any]:
    rec = hitl.consents.withdraw(consent_id, reason=reason)
    if not rec:
        raise HTTPException(status_code=404, detail="Consent not found or already withdrawn")
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="consent.withdraw",
        resource_type="consent",
        resource_id=consent_id,
    )
    return rec.to_dict()


@app.post("/v1/consents/evaluate-operation")
def evaluate_operation(
    body: EvaluateBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        dest = ModelDestination(body.model_destination)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    decision = hitl.authorize_processing(
        matter_id=body.matter_id,
        subject_id=body.subject_id,
        categories=body.data_categories,
        purpose=body.purpose,
        model_destination=dest,
    )
    return decision.to_dict()


# ----- Phase 3 HITL: exceptions -----


class ExceptionBody(BaseModel):
    category: str = "OTHER"
    message: str
    severity: Optional[str] = None
    task_id: Optional[str] = None
    affected_artifacts: list[str] = Field(default_factory=list)


@app.post("/v1/matters/{matter_id}/exceptions")
def emit_exception(
    matter_id: str,
    body: ExceptionBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        kind = ExceptionKind(body.category)
    except ValueError:
        kind = ExceptionKind.MODEL_POLICY_VIOLATION
    sev = Severity(body.severity) if body.severity else None
    ev = hitl.exceptions.emit(
        matter_id=matter_id,
        kind=kind,
        message=body.message,
        severity=sev,
        task_id=body.task_id,
        affected_artifacts=body.affected_artifacts,
    )
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="exception.emit",
        matter_id=matter_id,
        resource_type="exception",
    )
    return ev.to_dict()


@app.get("/v1/matters/{matter_id}/exceptions")
def list_exceptions(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    return {
        "matter_id": matter_id,
        "export_frozen": hitl.exceptions.export_frozen(matter_id),
        "events": [e.to_dict() for e in hitl.exceptions.events if e.matter_id == matter_id],
    }


class ResolveBody(BaseModel):
    reason: str


@app.post("/v1/exceptions/{exception_id}/resolve")
def resolve_exception(
    exception_id: str,
    body: ResolveBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Resolve an exception. Actor identity derived from authenticated session, not request body."""
    try:
        ev = hitl.exceptions.resolve(
            exception_id, human_id=current_user.user_id, reason=body.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not ev:
        raise HTTPException(status_code=404, detail="Exception not found")
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="exception.resolve",
        resource_type="exception",
        resource_id=exception_id,
        detail={"reason": body.reason},
    )
    return ev.to_dict()


# ----- Phase 3 HITL: privilege production -----


class FreezeBody(BaseModel):
    output_class: str = "CLIENT_EXPORT"
    body: str
    document_ids: list[str] = Field(default_factory=list)
    derivative_texts: list[str] = Field(default_factory=list)
    recipient: str = ""


@app.post("/v1/matters/{matter_id}/productions/freeze")
def freeze_production(
    matter_id: str,
    body: FreezeBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        reject_if_public_demo("court-ready production freeze")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    check = enforce_public_text(body.body)
    if not check.get("ok", True):
        raise HTTPException(status_code=400, detail=check.get("error", "blocked"))
    try:
        oc = OutputClass(body.output_class)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    pkg = hitl.authorize_output(
        matter_id=matter_id,
        output_class=oc,
        body=body.body,
        document_ids=body.document_ids,
        derivative_texts=body.derivative_texts,
        recipient=body.recipient,
    )
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="production.freeze",
        matter_id=matter_id,
        resource_type="production",
    )
    return pkg.to_dict()


class ReviewBody(BaseModel):
    notes: str = ""


@app.post("/v1/productions/{production_id}/review")
def review_production(
    production_id: str,
    body: ReviewBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Review a production. Actor identity derived from authenticated session."""
    try:
        pkg = hitl.productions.mark_reviewed(
            production_id, reviewer_id=current_user.user_id, notes=body.notes
        )
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="production.review",
        resource_type="production",
        resource_id=production_id,
    )
    return pkg.to_dict()


class ApproveBody(BaseModel):
    notes: str = ""
    same_person_override: bool = False
    same_person_override_reason: str = ""


@app.post("/v1/productions/{production_id}/approve")
def approve_production(
    production_id: str,
    body: ApproveBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Approve a production. Approver identity derived from authenticated session."""
    try:
        pkg = hitl.productions.approve(
            production_id,
            approver_id=current_user.user_id,
            notes=body.notes,
            same_person_override=body.same_person_override,
            same_person_override_reason=body.same_person_override_reason,
        )
    except (KeyError, ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="production.approve",
        resource_type="production",
        resource_id=production_id,
    )
    return pkg.to_dict()


@app.post("/v1/productions/{production_id}/release")
def release_production(
    production_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    try:
        reject_if_public_demo("court-ready document export/release")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    try:
        pkg = hitl.productions.release(production_id)
    except (KeyError, PermissionError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="production.release",
        resource_type="production",
        resource_id=production_id,
    )
    return pkg.to_dict()


# ----- Deadlines / JR clock -----


class JrClockBody(BaseModel):
    matter_id: str
    issuance_date: Optional[str] = None
    finality_known: bool = True
    enabling_act_known: bool = True
    extension_sought: bool = False


@app.post("/v1/deadlines/jr-clock")
def jr_clock(
    body: JrClockBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Calculate JR clock. Requires authentication and matter authorization; human_confirmed removed."""
    matter_id = require_matter_access(current_user, body.matter_id)
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="deadline.jr_clock",
        org_id=current_user.org_id,
        matter_id=matter_id,
        resource_type="deadline",
    )
    return calculate_jr_clock(
        JrClockRequest(
            matter_id=matter_id,
            issuance_date=body.issuance_date,
            finality_known=body.finality_known,
            enabling_act_known=body.enabling_act_known,
            extension_sought=body.extension_sought,
            human_confirmed=False,  # Must be a separate authenticated approval event
        )
    ).to_dict()


class DeadlineBody(BaseModel):
    matter_id: str
    label: str
    start_date: Optional[str] = None
    service_method: Optional[str] = None
    window_days: Optional[int] = None
    synthetic: bool = False
    statutory_basis: str = ""


@app.post("/v1/deadlines/calculate")
def deadline_calculate(
    body: DeadlineBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Fail-closed provisional deadline. Requires matter authorization."""
    matter_id = require_matter_access(current_user, body.matter_id)
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="deadline.calculate",
        org_id=current_user.org_id,
        matter_id=matter_id,
        resource_type="deadline",
    )
    return calculate_deadline(
        matter_id=matter_id,
        label=body.label,
        start_date=body.start_date,
        service_method=body.service_method,
        window_days=body.window_days,
        human_confirmed=False,  # Must be a separate authenticated approval event
        synthetic=body.synthetic,
        statutory_basis=body.statutory_basis,
    ).to_dict()


# ----- Phase 4-4 post-resolution -----


class DecisionIngestBody(BaseModel):
    text: str
    decision_date: Optional[str] = None
    predicted_summary: str = ""
    predicted_classes: list[str] = Field(default_factory=list)
    client_role: str = "tenant"
    run_compliance: bool = True
    open_jr_if_unfavorable: bool = True


@app.post("/v1/matters/{matter_id}/post-resolution/ingest")
def ingest_decision(
    matter_id: str,
    body: DecisionIngestBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Full 4-4 entry: parse decision → clocks → compliance seed → optional JR."""
    try:
        reject_if_public_demo("persistent post-resolution ingest")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    check = enforce_public_text(body.text)
    if not check.get("ok", True):
        raise HTTPException(status_code=400, detail=check.get("error"))
    out = post_resolution.ingest_decision(
        matter_id=matter_id,
        text=body.text,
        decision_date=body.decision_date,
        predicted_summary=body.predicted_summary,
        predicted_classes=body.predicted_classes or None,
    )
    rec = post_resolution.outcomes.get(matter_id)
    result: dict[str, Any] = {"outcome": out}

    if body.run_compliance and rec:
        events = post_resolution.compliance.detect_non_compliance(
            matter_id, rec.clocks
        )
        tickets = []
        kinds = {o.obligation_id: o.kind.value for o in rec.obligations}
        for ev in events:
            t = post_resolution.escalations.route_event(
                ev, obligation_kind=kinds.get(ev.obligation_id)
            )
            tickets.append(t.to_dict())
        result["non_compliance"] = [e.to_dict() for e in events]
        result["escalations"] = tickets

    if body.open_jr_if_unfavorable and rec:
        jr = post_resolution.jr.trigger(
            matter_id=matter_id,
            decision_date=body.decision_date or rec.decision_date or "",
            decision_or_notes_text=body.text,
            client_role=body.client_role,
            outcome_classes=rec.outcome_classes,
        )
        result["jr"] = jr
        if jr.get("unfavorable_trigger"):
            stay = post_resolution.stays.generate(
                matter_id, vacate_date=body.decision_date or ""
            )
            result["stay"] = stay.to_dict()

    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="post_resolution.ingest",
        matter_id=matter_id,
        resource_type="post_resolution",
    )
    return result


@app.get("/v1/matters/{matter_id}/post-resolution")
def get_post_resolution(
    matter_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    rec = post_resolution.outcomes.get(matter_id)
    return {
        "matter_id": matter_id,
        "outcome": rec.to_dict() if rec else None,
        "compliance_entries": [
            e.to_dict()
            for e in post_resolution.compliance.ledger.for_matter(matter_id)
        ],
        "escalations": [
            t.to_dict()
            for t in post_resolution.escalations.tickets
            if t.matter_id == matter_id
        ],
        "jr_clock": post_resolution.jr.clocks.get(matter_id).to_dict()
        if matter_id in post_resolution.jr.clocks
        else None,
        "petition": post_resolution.jr.petitions.get(matter_id).to_dict()
        if matter_id in post_resolution.jr.petitions
        else None,
    }


class EnforcementBody(BaseModel):
    package_type: str = "RTB_ENFORCEMENT"
    order_summary: str = ""
    amount: Optional[float] = None


@app.post("/v1/matters/{matter_id}/post-resolution/enforcement")
def build_enforcement(
    matter_id: str,
    body: EnforcementBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    packer = post_resolution.enforcement
    try:
        pt = PackageType(body.package_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if pt == PackageType.RTB_ENFORCEMENT:
        pkg = packer.build_rtb_enforcement(
            matter_id, order_summary=body.order_summary
        )
    elif pt == PackageType.PROVINCIAL_COURT_MONETARY:
        pkg = packer.build_provincial_court_monetary(matter_id, amount=body.amount)
    else:
        pkg = packer.build_garnishment(matter_id)
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="post_resolution.enforcement",
        matter_id=matter_id,
        resource_type="enforcement",
    )
    return pkg.to_dict()


class CloseMatterBody(BaseModel):
    closed_on: str
    final_summary: str
    object_refs: dict[str, list[str]] = Field(default_factory=dict)


@app.post("/v1/matters/{matter_id}/post-resolution/close")
def close_matter(
    matter_id: str,
    body: CloseMatterBody,
    current_user: CurrentUser,
) -> dict[str, Any]:
    plan = post_resolution.retention.close_matter(
        matter_id=matter_id,
        closed_on=body.closed_on,
        final_summary=body.final_summary,
        object_refs=body.object_refs or None,
    )
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="post_resolution.close",
        matter_id=matter_id,
        resource_type="post_resolution",
    )
    return plan.to_dict()


# ----- knowledge -----


@app.get("/v1/knowledge/sources")
def knowledge_sources(
    current_user: CurrentUser,
) -> dict[str, Any]:
    from knowledgebase.source_registry import SourceRegistry

    reg = SourceRegistry()
    return {"sources": [s.to_dict() for s in reg.sources]}


@app.post("/v1/knowledge/citations/verify")
def verify_cite(
    body: dict[str, str],
    current_user: CurrentUser,
) -> dict[str, Any]:
    from knowledgebase.citation_verifier import verify_citation

    raw = body.get("citation") or body.get("raw") or ""
    result = verify_citation(raw).to_dict()
    get_audit_ledger().append(
        actor_id=current_user.user_id,
        action="knowledge.citation.verify",
        resource_type="citation",
        detail={"citation_text": raw, "status": result.get("status")},
    )
    return result
