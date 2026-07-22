"""Template library — Form 66 = Petition; Form 67 = Response to Petition (Rule 16-1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TemplateSpec:
    template_id: str
    title: str
    category: str
    path_hint: str
    form_code: str = ""
    form_number: str = ""
    document_type: str = ""
    forum: str = ""
    source_rule: str = ""
    status: str = "CURRENT"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "title": self.title,
            "category": self.category,
            "path_hint": self.path_hint,
            "form_code": self.form_code,
            "form_number": self.form_number,
            "document_type": self.document_type,
            "forum": self.forum,
            "source_rule": self.source_rule,
            "status": self.status,
            "notes": self.notes,
        }


CATALOG: list[TemplateSpec] = [
    TemplateSpec(
        template_id="bcsc_form_66_jr",
        title="Petition (Form 66) — JR / petition proceedings",
        category="jr",
        path_hint="templates/petition/",
        form_code="Form 66",
        form_number="66",
        document_type="PETITION",
        forum="BC_SUPREME_COURT",
        source_rule="Rule 16-1",
        notes=(
            "Petition proceedings commence with Form 66. "
            "Do NOT label Form 67 as the judicial-review petition."
        ),
    ),
    TemplateSpec(
        template_id="bcsc_form_67_response",
        title="Response to Petition (Form 67)",
        category="jr",
        path_hint="knowledgebase/templates/jr/",
        form_code="Form 67",
        form_number="67",
        document_type="RESPONSE_TO_PETITION",
        forum="BC_SUPREME_COURT",
        source_rule="Rule 16-1",
        notes="Response to petition — not the originating petition.",
    ),
    TemplateSpec(
        template_id="bcsc_form_32",
        title="Notice of Application (Form 32)",
        category="application",
        path_hint="knowledgebase/templates/jr/",
        form_code="Form 32",
        form_number="32",
        document_type="NOTICE_OF_APPLICATION",
        forum="BC_SUPREME_COURT",
    ),
    TemplateSpec(
        template_id="bcsc_form_109",
        title="Affidavit (Form 109)",
        category="affidavit",
        path_hint="knowledgebase/templates/affidavit/",
        form_code="Form 109",
        form_number="109",
        document_type="AFFIDAVIT",
        forum="BC_SUPREME_COURT",
    ),
    TemplateSpec(
        template_id="JR-STAY",
        title="Stay application outline",
        category="stay",
        path_hint="knowledgebase/templates/jr/stay.md",
        notes="Three-part test — human legal judgment required.",
    ),
    TemplateSpec(
        template_id="RTB-DISPUTE-INDEX",
        title="RTB forms index (official site)",
        category="rtb",
        path_hint="knowledgebase/templates/rtb/README.md",
        notes="Always download current form from RTB / gov.bc.ca.",
    ),
    TemplateSpec(
        template_id="EVIDENCE-BINDER",
        title="Evidence binder index template",
        category="evidence_binder",
        path_hint="knowledgebase/templates/evidence_binder/README.md",
    ),
]


def list_templates(category: str | None = None) -> list[TemplateSpec]:
    if not category:
        return list(CATALOG)
    return [t for t in CATALOG if t.category == category]


def petition_form() -> TemplateSpec:
    """Canonical JR petition form — Form 66."""
    return next(t for t in CATALOG if t.form_number == "66")
