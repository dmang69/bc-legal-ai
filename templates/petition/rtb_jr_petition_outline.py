"""
JR petition outline — patent unreasonableness + procedural fairness.

Structure supplied by principal. Authorities and pins require verification
on BC Laws / CanLII and the official transcript before filing.
"""

from __future__ import annotations

from architecture.petition import (
    JRStandardLabel,
    PetitionCite,
    PetitionGround,
    PetitionOutline,
    PetitionSubGround,
)


def rtb_jr_petition_outline(*, matter_id: str | None = None) -> PetitionOutline:
    """
    PETITION OUTLINE:
      GROUND 1: Patent Unreasonableness (1a–1c)
      GROUND 2: Procedural Fairness Violation (2a–2b)
    """
    return PetitionOutline(
        outline_id="PET-JR-RTB-001",
        title="PETITION OUTLINE",
        matter_id=matter_id,
        court="BC Supreme Court",
        statute_route="Judicial Review Procedure Act",
        related_legal_tests=["RTA-s56-retaliatory-eviction"],
        grounds=[
            PetitionGround(
                ground_id="1",
                title="Patent Unreasonableness",
                standard=JRStandardLabel.PATENT_UNREASONABLENESS,
                sub_grounds=[
                    PetitionSubGround(
                        sub_id="1a",
                        description=(
                            'Arbitrator accepted "400 police calls" as evidence of illegal '
                            "activity without requiring breakdown of call outcomes"
                        ),
                        cites=[
                            PetitionCite(
                                kind="evidence",
                                label="EM-031",
                                evidence_node_id="EM-031",
                                detail="RCMP letter — no outcome data",
                            ),
                            PetitionCite(
                                kind="transcript",
                                label="Transcript",
                                transcript_start="25:40",
                                transcript_end="26:40",
                            ),
                        ],
                    ),
                    PetitionSubGround(
                        sub_id="1b",
                        description=(
                            "Arbitrator failed to distinguish between calls FOR service "
                            "and CONFIRMED illegal activity"
                        ),
                        cites=[
                            PetitionCite(
                                kind="authority",
                                label="RTA s. 47",
                                citation_short=(
                                    "RTA s. 47 — requires engagement in illegal activity "
                                    "(VERIFY wording and applicability on BC Laws)"
                                ),
                                verification_status="UNVERIFIED",
                            ),
                            PetitionCite(
                                kind="authority",
                                label="R. v. Grant",
                                citation_short=(
                                    "R. v. Grant — analogous on reliability of police contact data "
                                    "(VERIFY citation and principle on CanLII; confirm fit)"
                                ),
                                verification_status="UNVERIFIED",
                            ),
                        ],
                        notes=(
                            "Analogous criminal authority — map carefully to RTB civil standard; "
                            "do not overstate. Run UNVERIFIED CITATION FLAG before court-ready draft."
                        ),
                    ),
                    PetitionSubGround(
                        sub_id="1c",
                        description=(
                            'Arbitrator accepted "nuisance property" designation without '
                            "any documentary evidence"
                        ),
                        cites=[
                            PetitionCite(
                                kind="transcript",
                                label="Transcript",
                                transcript_start="37:00",
                                detail="assertion only",
                            ),
                            PetitionCite(
                                kind="authority",
                                label="Weichelt v. Leary",
                                citation_short="Weichelt v. Leary, 2021 BCSC 1783",
                                detail=(
                                    "Evidentiary sufficiency requirements "
                                    "(VERIFY pinpoints and holding on CanLII)"
                                ),
                                verification_status="UNVERIFIED",
                            ),
                        ],
                        notes=(
                            "Contrary to evidentiary sufficiency requirements pleaded from "
                            "Weichelt — confirm paragraphs supporting the proposition before filing."
                        ),
                    ),
                ],
            ),
            PetitionGround(
                ground_id="2",
                title="Procedural Fairness Violation",
                standard=JRStandardLabel.PROCEDURAL_FAIRNESS,
                sub_grounds=[
                    PetitionSubGround(
                        sub_id="2a",
                        description=(
                            "Arbitrator failed to assist self-represented tenant with "
                            "evidentiary service requirements"
                        ),
                        cites=[
                            PetitionCite(
                                kind="transcript",
                                label="Transcript",
                                transcript_start="10:21",
                                transcript_end="14:14",
                            ),
                            PetitionCite(
                                kind="authority",
                                label="Grewal v. British Columbia (Residential Tenancy Branch)",
                                citation_short=(
                                    "Grewal v. British Columbia (Residential Tenancy Branch), "
                                    "2017 BCCA 67"
                                ),
                                verification_status="UNVERIFIED",
                            ),
                        ],
                        notes=(
                            "Map SRL assistance / fairness principles from Grewal to facts; "
                            "verify holding and paragraphs on CanLII."
                        ),
                    ),
                    PetitionSubGround(
                        sub_id="2b",
                        description=(
                            "Arbitrator excluded tenant's emails to mayor/bylaw without "
                            "providing clear explanation or remedy opportunity"
                        ),
                        cites=[
                            PetitionCite(
                                kind="transcript",
                                label="Transcript",
                                transcript_start="57:18",
                                transcript_end="59:38",
                            ),
                        ],
                    ),
                ],
            ),
        ],
        notes=(
            "Standard of review: plead as structured; confirm whether patent unreasonableness "
            "or reasonableness (Vavilov / RTA / JRPA) is the correct label for this decision. "
            "Link EM-031 to sequential EvidenceNode before hearing package. "
            "All authorities listed as UNVERIFIED until CitationDB verification."
        ),
    )
