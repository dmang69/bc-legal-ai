"""Cross-reference helpers — contradictions, corroboration candidates, chronology."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

from architecture.schemas import EvidenceItem

# Keyword → claim_tag suggestions (first-pass; human may override)
CLAIM_TAG_LEXICON: list[tuple[str, list[str]]] = [
    ("mold_hazard", [r"\bmold\b", r"\bmould\b", r"\bmildew\b", r"\bspore"]),
    ("non_repair", [r"\brepair", r"\bunfixed\b", r"\bnot complied\b", r"\bfail(ed|ure)? to (fix|maintain)"]),
    ("retaliatory_eviction", [r"\bretaliat", r"\beviction after complaint", r"\bnotice to end"]),
    ("rent_issue", [r"\brent\b", r"\barrears\b", r"\bnon[-\s]?payment"]),
    ("quiet_enjoyment", [r"\bquiet enjoyment\b", r"\bharass", r"\bunlawful entr"]),
    ("deposit", [r"\bdeposit\b", r"\bsecurity\b", r"\bpet deposit"]),
    ("entry", [r"\bentry\b", r"\b24 hour", r"\bwithout notice"]),
    ("city_enforcement", [r"\bcity fine\b", r"\bbylaw\b", r"\binspection"]),
    ("official_order", [r"\brtb\b", r"\barbitrator\b", r"\border of possession\b", r"\bdecision"]),
]

FILENAME_TS = re.compile(
    r"(?P<y>20\d{2})(?P<m>\d{2})(?P<d>\d{2})(?:[_-]?(?P<h>\d{2})(?P<mi>\d{2})(?P<s>\d{2}))?"
)
ISO_DATE = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")


def suggest_claim_tags(text: str) -> list[str]:
    low = (text or "").lower()
    tags: list[str] = []
    for tag, pats in CLAIM_TAG_LEXICON:
        if any(re.search(p, low) for p in pats):
            tags.append(tag)
    return tags


def parse_date_hint(source_file: str, date_captured: Optional[str] = None) -> Optional[date]:
    if date_captured:
        m = ISO_DATE.search(date_captured)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                pass
        try:
            return date.fromisoformat(date_captured[:10])
        except ValueError:
            pass
    m = FILENAME_TS.search(source_file or "")
    if m:
        try:
            return date(int(m.group("y")), int(m.group("m")), int(m.group("d")))
        except ValueError:
            return None
    return None


@dataclass
class TemporalConflict:
    claim_tag: str
    earlier_id: str
    later_id: str
    earlier_date: str
    later_date: str
    note: str

    def to_dict(self) -> dict:
        return {
            "claim_tag": self.claim_tag,
            "earlier_id": self.earlier_id,
            "later_id": self.later_id,
            "earlier_date": self.earlier_date,
            "later_date": self.later_date,
            "note": self.note,
        }


def detect_temporal_conflicts(items: list[EvidenceItem]) -> list[TemporalConflict]:
    """
    Flag when multiple items share a claim_tag but dates suggest conflict
    (e.g. 'fixed' narrative vs later photo still showing defect).

    Heuristic only — human must confirm.
    """
    by_tag: dict[str, list[tuple[EvidenceItem, date]]] = {}
    for e in items:
        d = parse_date_hint(e.source_file, e.date_captured)
        if d is None:
            continue
        for tag in e.claim_tags:
            by_tag.setdefault(tag, []).append((e, d))

    conflicts: list[TemporalConflict] = []
    for tag, pairs in by_tag.items():
        if len(pairs) < 2:
            continue
        pairs_sorted = sorted(pairs, key=lambda x: x[1])
        # If any later item notes ongoing condition while earlier claims repair, flag span
        first, first_d = pairs_sorted[0]
        last, last_d = pairs_sorted[-1]
        if first_d == last_d:
            continue
        notes = (first.human_notes + " " + last.human_notes).lower()
        sources = (first.source_file + " " + last.source_file).lower()
        repairish = any(
            w in notes or w in sources
            for w in ("fixed", "repaired", "remediated", "complied")
        )
        ongoing = any(
            w in notes or w in sources
            for w in ("ongoing", "still", "mold", "mould", "not_complied", "unfixed")
        )
        if repairish or ongoing or tag in ("mold_hazard", "non_repair"):
            conflicts.append(
                TemporalConflict(
                    claim_tag=tag,
                    earlier_id=first.id,
                    later_id=last.id,
                    earlier_date=first_d.isoformat(),
                    later_date=last_d.isoformat(),
                    note=(
                        f"Date span on '{tag}': {first_d} → {last_d}. "
                        "Review for temporal conflict (repair claim vs later evidence)."
                    ),
                )
            )
    return conflicts


def detect_corroboration_candidates(
    items: list[EvidenceItem],
    *,
    min_shared_tags: int = 1,
) -> list[tuple[str, str, list[str]]]:
    """Pairs that share claim_tags (and optionally location) — candidates to link."""
    out: list[tuple[str, str, list[str]]] = []
    for i, a in enumerate(items):
        for b in items[i + 1 :]:
            if a.id in a.corroborates and b.id in a.corroborates:
                continue
            shared = sorted(set(a.claim_tags) & set(b.claim_tags))
            if len(shared) < min_shared_tags:
                continue
            if (
                a.location_referenced
                and b.location_referenced
                and a.location_referenced.strip().lower()
                != b.location_referenced.strip().lower()
            ):
                continue
            out.append((a.id, b.id, shared))
    return out


@dataclass
class ChronologyEntry:
    sort_date: Optional[str]
    evidence_id: str
    source_file: str
    claim_tags: list[str]
    note: str

    def format_line(self) -> str:
        d = self.sort_date or "date unknown"
        tags = ", ".join(self.claim_tags) if self.claim_tags else "untagged"
        return f"{d} — {self.source_file} (id={self.evidence_id[:8]}…; tags: {tags}){self.note}"


def build_chronology(items: list[EvidenceItem]) -> list[ChronologyEntry]:
    entries: list[ChronologyEntry] = []
    for e in items:
        d = parse_date_hint(e.source_file, e.date_captured)
        note = f" — {e.human_notes}" if e.human_notes else ""
        entries.append(
            ChronologyEntry(
                sort_date=d.isoformat() if d else None,
                evidence_id=e.id,
                source_file=e.source_file,
                claim_tags=list(e.claim_tags),
                note=note,
            )
        )
    entries.sort(key=lambda x: (x.sort_date is None, x.sort_date or "", x.source_file))
    return entries


def format_chronology_markdown(items: list[EvidenceItem]) -> str:
    lines = ["## Chronology (source-linked)", ""]
    for entry in build_chronology(items):
        lines.append(f"- {entry.format_line()}")
    if len(lines) == 2:
        lines.append("- *(no evidence rows)*")
    lines.append("")
    lines.append(
        "> Dates from EXIF/`date_captured`/filename patterns are **candidates** — verify against the record."
    )
    return "\n".join(lines)
