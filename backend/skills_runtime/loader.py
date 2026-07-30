"""
Load and route in-repo legal skills (skills/*/SKILL.md) for the chat orchestrator.

No network. No model weights. Skills are markdown operating procedures that
ground supervised, deterministic workspace replies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Optional

# backend/skills_runtime/loader.py → repo root = parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_ROOT = _REPO_ROOT / "skills"

# Canonical specialist → skill folder names (under skills/)
SPECIALIST_SKILLS: dict[str, list[str]] = {
    "bc_legal_associate": [
        "supreme-court-civil-counsel",
        "bc-judicial-review-guide",
        "bc-tenancy-substantive",
        "bc-tenancy-procedure",
    ],
    "rtb_specialist": [
        "bc-tenancy-substantive",
        "bc-tenancy-procedure",
        "bc-tenancy-advocacy",
    ],
    "jr_counsel": [
        "bc-judicial-review-guide",
        "supreme-court-civil-counsel",
        "administrative-law-canada",
    ],
    "statutory_interpreter": [
        "statutory-interpretation",
        "bc-legislation-admin",
    ],
    "legal_terminology": [
        "legal-terminology-core",
    ],
    "evidence_analyst": [
        "evidence-law-canada",
        "critical-reading",
    ],
    "citation_clerk": [
        "canlii-boa-builder",
        "supreme-court-civil-counsel",
    ],
    "procedural_clerk": [
        "bc-tenancy-procedure",
        "supreme-court-civil-counsel",
    ],
    "deadline_clerk": [
        "bc-judicial-review-guide",
        "bc-tenancy-procedure",
    ],
    "affidavit_drafter": [
        "evidence-law-canada",
        "supreme-court-civil-counsel",
    ],
    "boa_builder": [
        "canlii-boa-builder",
        "supreme-court-civil-counsel",
    ],
    "cross_exam_planner": [
        "evidence-law-canada",
        "critical-reading",
        "tribunal-hearing-prep",
    ],
    "hearing_prep": [
        "tribunal-hearing-prep",
        "bc-tenancy-procedure",
        "bc-judicial-review-guide",
        "evidence-law-canada",
        "critical-reading",
        "supreme-court-civil-counsel",
    ],
    "devils_advocate": [
        "argument-architecture",
        "critical-reading",
        "supreme-court-civil-counsel",
    ],
    "privilege_sentinel": [
        "evidence-law-canada",
        "supreme-court-civil-counsel",
    ],
    "client_intake": [
        "bc-tenancy-procedure",
        "supreme-court-civil-counsel",
    ],
    "enforcement_assistant": [
        "bc-tenancy-substantive",
        "bc-tenancy-procedure",
    ],
}

# Keyword routing overlays skill packs on top of specialist
KEYWORD_SKILLS: list[tuple[tuple[str, ...], list[str]]] = [
    (
        ("judicial review", "form 66", "form 67", "jrpa", "petition", "order of possession", "patent unreason"),
        ["bc-judicial-review-guide", "supreme-court-civil-counsel", "tribunal-hearing-prep"],
    ),
    (
        (
            "hearing prep",
            "hearing preparation",
            "witness prep",
            "witness coach",
            "tabbed binder",
            "binder index",
            "dissect the decision",
            "dissect the record",
            "tribunal hearing",
            "simulate q&a",
            "cross-examination prep",
            "opening statement",
        ),
        ["tribunal-hearing-prep", "evidence-law-canada", "critical-reading"],
    ),
    (
        ("rtb", "tenancy", "landlord", "tenant", "notice to end", "residential tenancy"),
        ["bc-tenancy-substantive", "bc-tenancy-procedure"],
    ),
    (
        ("book of authorities", "canlii", "authorities table", "boa"),
        ["canlii-boa-builder", "supreme-court-civil-counsel"],
    ),
    (
        ("affidavit", "exhibit", "hearsay", "privilege", "form 109"),
        ["evidence-law-canada", "supreme-court-civil-counsel"],
    ),
    (
        ("deadline", "limitation", "60 day", "s.57", "ata s.57"),
        ["bc-judicial-review-guide"],
    ),
    (
        ("vavilov", "standard of review", "procedural fairness", "baker"),
        ["bc-judicial-review-guide", "administrative-law-canada"],
    ),
]

LOCKED_GUARDS = [
    "Consent is not privilege.",
    "Consent withdrawal is not unconditional deletion (BC PIPA).",
    "Form 66 commences a petition; Form 67 is the response; interlocutory ≈ Form 32/33; affidavit ≈ Form 109.",
    "JR clock (when ATA s.57 applies): 60 days from issuance of the final decision; s.57(2) extension is not automatic; alternatives when uncertain.",
    "Honest encryption: on-device analysis or controlled server decrypt with consent — not both contradictory claims.",
    "RTB published archive is a subset; absence is not proof a decision never existed.",
]


@dataclass(frozen=True)
class SkillDoc:
    name: str
    path: str
    description: str
    version: str
    body: str
    related: list[str] = field(default_factory=list)

    def excerpt(self, max_chars: int = 2800) -> str:
        text = self.body.strip()
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 20].rstrip() + "\n\n[… skill truncated for context window …]"

    def to_summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "description": self.description,
            "version": self.version,
            "related": list(self.related),
            "chars": len(self.body),
        }


def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end < 0:
        return {}, raw
    fm_raw = raw[3:end].strip()
    body = raw[end + 4 :].lstrip("\n")
    meta: dict[str, Any] = {}
    # Minimal YAML-ish parse (avoid requiring PyYAML for runtime import side effects)
    key = None
    buf: list[str] = []
    for line in fm_raw.splitlines():
        if not line.strip():
            continue
        if line.startswith(" ") and key:
            buf.append(line.strip().strip("\"'"))
            continue
        if ":" in line and not line.strip().startswith("-"):
            if key and buf:
                meta[key] = " ".join(buf).strip()
                buf = []
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.strip()
            if v in (">", "|"):
                buf = []
            elif v:
                meta[key] = v.strip("\"'")
                key = None
            else:
                buf = []
        elif line.strip().startswith("-") and key:
            buf.append(line.strip()[1:].strip().strip("\"'"))
    if key and buf:
        meta[key] = " ".join(buf).strip()
    return meta, body


def skills_root() -> Path:
    return _SKILLS_ROOT


def list_skill_dirs() -> list[Path]:
    root = skills_root()
    if not root.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(root.iterdir()):
        if p.is_dir() and (p / "SKILL.md").is_file():
            out.append(p)
    return out


@lru_cache(maxsize=1)
def load_all_skills() -> dict[str, SkillDoc]:
    docs: dict[str, SkillDoc] = {}
    for d in list_skill_dirs():
        raw = (d / "SKILL.md").read_text(encoding="utf-8", errors="replace")
        meta, body = _parse_frontmatter(raw)
        name = str(meta.get("name") or d.name).strip()
        related_raw = meta.get("related") or meta.get("related_skills") or ""
        if isinstance(related_raw, list):
            related = [str(x) for x in related_raw]
        else:
            related = [x.strip() for x in re.split(r"[,\[\]\s]+", str(related_raw)) if x.strip()]
        docs[name] = SkillDoc(
            name=name,
            path=str((d / "SKILL.md").relative_to(_REPO_ROOT).as_posix()),
            description=str(meta.get("description") or "")[:1024],
            version=str(meta.get("version") or ""),
            body=body,
            related=related,
        )
    return docs


def clear_skill_cache() -> None:
    load_all_skills.cache_clear()


def get_skill(name: str) -> Optional[SkillDoc]:
    return load_all_skills().get(name)


def resolve_skills(
    *,
    specialist: str = "bc_legal_associate",
    message: str = "",
    explicit: Optional[Iterable[str]] = None,
    limit: int = 4,
) -> list[SkillDoc]:
    """Pick ordered unique skills for this turn."""
    catalog = load_all_skills()
    ordered: list[str] = []

    def add(names: Iterable[str]) -> None:
        for n in names:
            n = n.strip()
            if n and n in catalog and n not in ordered:
                ordered.append(n)

    if explicit:
        add(explicit)
    add(SPECIALIST_SKILLS.get(specialist or "", []))
    low = (message or "").lower()
    for keys, names in KEYWORD_SKILLS:
        if any(k in low for k in keys):
            add(names)

    # Always ensure counsel framework available when any court skill loaded
    if any(n in ordered for n in ("bc-judicial-review-guide", "canlii-boa-builder")):
        add(["supreme-court-civil-counsel"])

    return [catalog[n] for n in ordered[: max(1, limit)]]


def build_skill_context_block(skills: list[SkillDoc], *, per_skill_chars: int = 1800) -> str:
    if not skills:
        return ""
    parts = [
        "## Active skill pack (loaded from repo)",
        "",
        "Apply analytical category labels (FACT / ALLEGATION / LEGAL ARGUMENT / "
        "INFERENCE / ASSUMPTION / PROCEDURAL HISTORY / RECOMMENDATION). "
        "Fail-closed citations. Working drafts are not court-ready without human gate.",
        "",
        "### Locked design corrections",
    ]
    for g in LOCKED_GUARDS:
        parts.append(f"- {g}")
    parts.append("")
    for sk in skills:
        parts.append(f"### Skill: `{sk.name}` (v{sk.version or '?'})")
        if sk.description:
            parts.append(sk.description.strip())
        parts.append("")
        parts.append(sk.excerpt(per_skill_chars))
        parts.append("")
    return "\n".join(parts).strip()


def catalog_summary() -> dict[str, Any]:
    docs = load_all_skills()
    return {
        "skills_root": str(skills_root().as_posix()),
        "count": len(docs),
        "skills": [d.to_summary() for d in docs.values()],
        "specialist_map": {k: v for k, v in SPECIALIST_SKILLS.items()},
        "locked_guards": list(LOCKED_GUARDS),
    }
