"""
Matter session — isolates one legal matter and exposes the associate workflow surface.

Privilege boundary: every operation is scoped to matter_id.
Does not file, send, or auto-waive privilege.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from architecture.evidence_node import EvidenceNode
from architecture.schemas import EvidenceItem, LegalArgument, Matter
from backend.evidence.crossref import (
    detect_corroboration_candidates,
    detect_temporal_conflicts,
    format_chronology_markdown,
)
from backend.evidence.ingest import ingest_bytes, ingest_text_record
from backend.evidence.matrix import EvidenceMatrix
from backend.evidence.nodes import EvidenceNodeStore, sync_items_to_nodes
from backend.evidence.gap_detection import (
    build_gap_detection_report,
    format_gap_detection_report,
)
from backend.evidence.timeline_engine import (
    build_timeline_from_nodes,
    format_timeline_markdown,
)
from backend.privilege.production_gate import (
    ProductionDecision,
    export_items_from_evidence,
    run_production_gate,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MatterMeta:
    matter_id: str
    title: str
    parties: list[str] = field(default_factory=list)
    tribunal_or_court: Optional[str] = None
    file_numbers: list[str] = field(default_factory=list)
    claimed_tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_matter(self) -> Matter:
        return Matter(
            title=self.title,
            tribunal_or_court=self.tribunal_or_court,
            file_numbers=list(self.file_numbers),
            parties=list(self.parties),
            legal_issues=list(self.claimed_tags),
            id=self.matter_id,
        )


class MatterSession:
    """One matter workspace: meta + evidence matrix + analysis reports."""

    def __init__(self, matter_id: str, *, root: Optional[Path] = None) -> None:
        if not matter_id or "/" in matter_id or "\\" in matter_id or ".." in matter_id:
            raise ValueError("matter_id must be path-safe")
        self.matter_id = matter_id
        self.root = (root or Path("matters")).resolve()
        self.matrix = EvidenceMatrix(matter_id, root=self.root)
        self.nodes = EvidenceNodeStore(matter_id, root=self.root)
        self._meta_path = self.root / matter_id / "matter.json"
        self.meta = self._load_or_create_meta()
        self.custodian_default = "tenant"

    @property
    def matter_dir(self) -> Path:
        return self.root / self.matter_id

    def _load_or_create_meta(self) -> MatterMeta:
        self.matter_dir.mkdir(parents=True, exist_ok=True)
        if self._meta_path.is_file():
            data = json.loads(self._meta_path.read_text(encoding="utf-8"))
            return MatterMeta(
                matter_id=data.get("matter_id", self.matter_id),
                title=data.get("title", self.matter_id),
                parties=list(data.get("parties") or []),
                tribunal_or_court=data.get("tribunal_or_court"),
                file_numbers=list(data.get("file_numbers") or []),
                claimed_tags=list(data.get("claimed_tags") or []),
                created_at=data.get("created_at", _utcnow()),
                updated_at=data.get("updated_at", _utcnow()),
            )
        meta = MatterMeta(matter_id=self.matter_id, title=self.matter_id)
        self._save_meta(meta)
        return meta

    def _save_meta(self, meta: Optional[MatterMeta] = None) -> None:
        m = meta or self.meta
        m.updated_at = _utcnow()
        self.matter_dir.mkdir(parents=True, exist_ok=True)
        self._meta_path.write_text(
            json.dumps(m.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def update(
        self,
        *,
        title: Optional[str] = None,
        parties: Optional[list[str]] = None,
        tribunal_or_court: Optional[str] = None,
        file_numbers: Optional[list[str]] = None,
        claimed_tags: Optional[list[str]] = None,
    ) -> MatterMeta:
        if title is not None:
            self.meta.title = title
        if parties is not None:
            self.meta.parties = list(parties)
        if tribunal_or_court is not None:
            self.meta.tribunal_or_court = tribunal_or_court
        if file_numbers is not None:
            self.meta.file_numbers = list(file_numbers)
        if claimed_tags is not None:
            self.meta.claimed_tags = list(claimed_tags)
        self._save_meta()
        return self.meta

    def ingest_file(
        self,
        filename: str,
        data: bytes,
        **kwargs: Any,
    ) -> EvidenceItem:
        custodian = kwargs.pop("custodian", self.custodian_default)
        item = ingest_bytes(self.matrix, filename=filename, data=data, **kwargs)
        for t in item.claim_tags:
            if t not in self.meta.claimed_tags:
                self.meta.claimed_tags.append(t)
        self.nodes.allocate_from_item(item, custodian=custodian)
        self._save_meta()
        return item

    def ingest_text(self, filename: str, text: str, **kwargs: Any) -> EvidenceItem:
        custodian = kwargs.pop("custodian", self.custodian_default)
        item = ingest_text_record(self.matrix, filename=filename, text=text, **kwargs)
        for t in item.claim_tags:
            if t not in self.meta.claimed_tags:
                self.meta.claimed_tags.append(t)
        self.nodes.allocate_from_item(
            item, extracted_text=text, custodian=custodian
        )
        self._save_meta()
        return item

    def sync_nodes(self) -> list[EvidenceNode]:
        return sync_items_to_nodes(
            self.matrix.all(),
            self.nodes,
            custodian=self.custodian_default,
        )

    def analysis_report(self) -> dict[str, Any]:
        items = self.matrix.all()
        # Ensure graph layer is current
        self.sync_nodes()
        gaps = self.matrix.gap_report(self.meta.claimed_tags)
        conflicts = [c.to_dict() for c in detect_temporal_conflicts(items)]
        corr = [
            {"a": a, "b": b, "shared_tags": tags}
            for a, b, tags in detect_corroboration_candidates(items)
        ]
        locked = [e.evidence_id for e in self.matrix.locked_for_export()]
        nodes = self.nodes.all()
        contra = self.nodes.run_contradiction_scan(persist=True)
        timeline = build_timeline_from_nodes(self.nodes.all())
        gap_report = build_gap_detection_report(timeline, matter_id=self.matter_id)
        strength = self.nodes.score_strength(persist=True)
        # Mirror scores onto matrix hearing_relevance
        from backend.evidence.strength import apply_strength_to_item

        node_by_matrix = {
            n.matrix_evidence_id: n for n in self.nodes.all() if n.matrix_evidence_id
        }
        for item in items:
            n = node_by_matrix.get(item.evidence_id)
            if n and n.strength_score is not None:
                from architecture.strength import assess_score

                apply_strength_to_item(item, assess_score(n.strength_score))
        self.matrix.save()
        return {
            "matter_id": self.matter_id,
            "title": self.meta.title,
            "summary": self.matrix.summary(),
            "nodes_summary": self.nodes.summary(),
            "node_ids": [n.node_id for n in nodes],
            "gaps": gaps,
            "temporal_conflicts": conflicts,
            "corroboration_candidates": corr,
            "key_fact_contradictions": contra.to_dict(),
            "timeline": [e.to_dict() for e in timeline],
            "timeline_markdown": format_timeline_markdown(timeline),
            "gap_detection": gap_report.to_dict(),
            "gap_detection_report": format_gap_detection_report(gap_report),
            "strength": {
                "buckets": strength["buckets"],
                "assessments": strength["assessments"],
            },
            "strength_report": strength["report"],
            "privilege_gated_ids": locked,
            "protected_nodes": [n.node_id for n in self.nodes.protected_nodes()],
            "chronology_markdown": format_chronology_markdown(items),
            "generated_at": _utcnow(),
        }

    def draft_argument_skeletons(self) -> list[dict[str, Any]]:
        """One LegalArgument skeleton per claimed tag with evidence IDs (not legal advice)."""
        from architecture.schemas import EvidenceRef

        out: list[dict[str, Any]] = []
        for tag in self.meta.claimed_tags:
            rows = self.matrix.by_claim_tag(tag)
            if not rows:
                arg = LegalArgument(
                    claim=f"Claim regarding {tag}",
                    evidence_gaps=[f"No evidence rows tagged {tag}"],
                    confidence=0.0,
                )
            else:
                arg = LegalArgument(
                    claim=f"Claim regarding {tag}",
                    factual_predicate=[
                        EvidenceRef(evidence_id=r.evidence_id, note=r.source_file)
                        for r in rows
                    ],
                    evidence_gaps=[],
                    confidence=min(0.85, 0.3 + 0.1 * len(rows)),
                )
            out.append(arg.to_dict())
        return out

    def query_api(self):
        """Evidence query facade over current graph nodes."""
        from backend.evidence.query import MatterQueryAPI

        self.sync_nodes()
        self.nodes.score_strength(persist=True)
        return MatterQueryAPI(self.nodes.all())

    def query_evidence(
        self,
        fact: str,
        *,
        min_strength: float = 0.5,
        include_contradictions: bool = True,
    ):
        return self.query_api().query_evidence(
            fact,
            min_strength=min_strength,
            include_contradictions=include_contradictions,
        )

    def query_timeline(
        self,
        *,
        start: Optional[str] = None,
        end: Optional[str] = None,
        event_types: Optional[list[str]] = None,
    ):
        return self.query_api().query_timeline(
            start=start, end=end, event_types=event_types
        )

    def query_gaps(self, claim: str, *, required_continuity: bool = True):
        return self.query_api().query_gaps(
            claim, required_continuity=required_continuity
        )

    def query_argument_support(
        self,
        legal_test: str,
        *,
        strategy: str = "MAXIMIZE_STRENGTH",
    ):
        return self.query_api().query_argument_support(
            legal_test, strategy=strategy
        )

    def grounding_gate(self):
        """Fail-closed gate: claims need evidence node + verified citation + inference chain."""
        from backend.grounding import build_gate_for_nodes
        from backend.grounding.citation_db import CitationDB, seed_bc_workbench_citations

        self.sync_nodes()
        db_path = self.matter_dir / "citations.json"
        db = CitationDB(path=db_path)
        if not db_path.is_file():
            seed_bc_workbench_citations(db)
            db.save()
        else:
            db.load()
        return build_gate_for_nodes(
            [n.node_id for n in self.nodes.all()],
            citation_db=db,
        )

    def ground_claim(self, claim) -> "object":
        """Evaluate a GroundedClaim; returns GroundingResult (may refuse)."""
        return self.grounding_gate().evaluate(claim)

    def evaluate_legal_test(self, test_id: str = "TEST-RETALIATORY-EVICTION-S56"):
        """Run a LegalTest against this matter's evidence graph."""
        from backend.legal_tests import default_legal_tests, evaluate_legal_test
        from backend.grounding.citation_db import CitationDB, seed_bc_workbench_citations

        tests = default_legal_tests()
        if test_id not in tests:
            raise KeyError(f"Unknown legal test: {test_id}")
        self.sync_nodes()
        self.nodes.score_strength(persist=True)
        db_path = self.matter_dir / "citations.json"
        db = CitationDB(path=db_path)
        if db_path.is_file():
            db.load()
        else:
            seed_bc_workbench_citations(db)
            db.save()
        return evaluate_legal_test(tests[test_id], self.nodes.all(), citation_db=db)

    def legal_test_report(self, test_id: str = "RTA-s56-retaliatory-eviction") -> str:
        """Narrative ELEMENT blocks for lawyer review."""
        return self.evaluate_legal_test(test_id).format_element_report()

    def add_examination_outline(self, outline) -> "Path":
        """Save an ExaminationOutline under this matter."""
        from pathlib import Path

        from backend.examination.service import save_outline

        outline.matter_id = self.matter_id
        return save_outline(outline, root=self.root)

    def load_examination_outline(self, outline_id: str):
        from backend.examination.service import load_outline

        return load_outline(self.matter_id, outline_id, root=self.root)

    def list_examination_outlines(self) -> list:
        from backend.examination.service import list_outlines

        return list_outlines(self.matter_id, root=self.root)

    def install_sanghera_cross_template(self) -> "Path":
        """Install the sample Sanghera cross outline (planning template)."""
        from templates.examination.sanghera_cross_outline import sanghera_cross_outline

        return self.add_examination_outline(
            sanghera_cross_outline(matter_id=self.matter_id)
        )

    def add_petition_outline(self, outline) -> "Path":
        from backend.petition.service import save_petition

        outline.matter_id = self.matter_id
        return save_petition(outline, root=self.root)

    def load_petition_outline(self, outline_id: str):
        from backend.petition.service import load_petition

        return load_petition(self.matter_id, outline_id, root=self.root)

    def list_petition_outlines(self) -> list:
        from backend.petition.service import list_petitions

        return list_petitions(self.matter_id, root=self.root)

    def install_jr_petition_template(self) -> "Path":
        """Install JR petition outline (patent unreasonableness + procedural fairness)."""
        from templates.petition.rtb_jr_petition_outline import rtb_jr_petition_outline

        return self.add_petition_outline(
            rtb_jr_petition_outline(matter_id=self.matter_id)
        )

    def save_tenancy_intake(self, intake) -> "Path":
        """Persist TenancyIntake and sync meta."""
        from backend.intake.service import apply_intake_to_matter_meta, save_intake

        intake.matter_id = self.matter_id
        apply_intake_to_matter_meta(self, intake)
        return save_intake(intake, root=self.root)

    def load_tenancy_intake(self):
        from backend.intake.service import load_intake

        return load_intake(self.matter_id, root=self.root)

    def intake_from_answers(self, answers: dict) -> "object":
        """Build + save intake from flat form/chat answers."""
        from backend.intake.service import intake_from_flat_answers

        intake = intake_from_flat_answers(answers, matter_id=self.matter_id)
        self.save_tenancy_intake(intake)
        return intake

    def production_check(
        self,
        *,
        evidence_ids: Optional[list[str]] = None,
        instructing_lawyer_signed: bool = False,
        client_waiver_signed: bool = False,
        intended_waiver: bool = False,
        destination: str = "export",
    ) -> ProductionDecision:
        items = self.matrix.all()
        if evidence_ids is not None:
            want = set(evidence_ids)
            items = [e for e in items if e.evidence_id in want]
        return run_production_gate(
            export_items_from_evidence(items),
            instructing_lawyer_signed=instructing_lawyer_signed,
            client_waiver_signed=client_waiver_signed,
            intended_waiver=intended_waiver,
            destination=destination,
        )

    def write_report(self) -> Path:
        report = self.analysis_report()
        report["argument_skeletons"] = self.draft_argument_skeletons()
        path = self.matter_dir / "analysis_report.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        chrono = self.matter_dir / "chronology.md"
        chrono.write_text(report["chronology_markdown"] + "\n", encoding="utf-8")
        tl = self.matter_dir / "timeline.md"
        tl.write_text(report.get("timeline_markdown", "") + "\n", encoding="utf-8")
        gap_path = self.matter_dir / "gap_detection_report.md"
        gap_path.write_text(report.get("gap_detection_report", "") + "\n", encoding="utf-8")
        strength_path = self.matter_dir / "strength_tiers.md"
        strength_path.write_text(report.get("strength_report", "") + "\n", encoding="utf-8")
        return path


def create_matter(
    title: str,
    *,
    matter_id: Optional[str] = None,
    root: Optional[Path] = None,
    parties: Optional[list[str]] = None,
    tribunal_or_court: Optional[str] = None,
) -> MatterSession:
    mid = matter_id or f"m-{uuid4().hex[:12]}"
    session = MatterSession(mid, root=root)
    session.update(
        title=title,
        parties=parties or [],
        tribunal_or_court=tribunal_or_court,
    )
    return session
