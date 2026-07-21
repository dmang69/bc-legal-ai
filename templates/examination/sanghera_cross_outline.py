"""
Example cross-examination outline — landlord's representative.

Content supplied by principal for hearing prep structure.
Expected answers are planning assumptions only.
Verify all transcript pins against the official transcript before use.
"""

from __future__ import annotations

from architecture.examination import (
    ExaminationOutline,
    ExaminationQuestion,
    QuestionPurpose,
    TranscriptPin,
)


def sanghera_cross_outline(*, matter_id: str | None = None) -> ExaminationOutline:
    """
    EXAMINATION OUTLINE — CROSS OF LANDLORD'S REPRESENTATIVE
    Target: Sukhbinder Sanghera
    Goal: Establish knowledge of co-tenant Natalie; undermine "400 calls" attribution
    """
    return ExaminationOutline(
        outline_id="EXAM-CROSS-SANGHERA-001",
        title="CROSS OF LANDLORD'S REPRESENTATIVE",
        target_witness="Sukhbinder Sanghera",
        goal=(
            "Establish knowledge of co-tenant Natalie, undermine "
            '"400 calls" attribution'
        ),
        exam_type="CROSS",
        matter_id=matter_id,
        related_legal_tests=["RTA-s56-retaliatory-eviction"],
        questions=[
            ExaminationQuestion(
                question_id="Q1",
                purpose=QuestionPurpose.FOUNDATIONAL,
                purpose_label="Foundational — establish her role",
                text=(
                    "You manage the property on behalf of your father, Gurmail Sanghera?"
                ),
                source_transcript=TranscriptPin(
                    timestamp="02:22",
                    source_label="Transcript",
                ),
                expected_answer="Yes",
                tags=["management", "agency", "foundational"],
            ),
            ExaminationQuestion(
                question_id="Q2",
                purpose=QuestionPurpose.LOCK_IN,
                purpose_label="Lock in lack of unit access",
                text=(
                    "Have you personally entered unit 990 in the last 12 months?"
                ),
                source_transcript=TranscriptPin(
                    timestamp="63:17",
                    quote="I have not entered the unit",
                    source_label="Transcript",
                ),
                expected_answer="No",
                tags=["unit_access", "knowledge", "990"],
            ),
            ExaminationQuestion(
                question_id="Q3",
                purpose=QuestionPurpose.CONFRONT,
                purpose_label="Confront with handwritten note",
                text=(
                    "I'm showing you a document dated December 2015, bearing what appears "
                    "to be your handwriting and your father's. It references two tenants — "
                    "myself and Natalie. Do you recognize this document?"
                ),
                source_evidence_nodes=["EM-019"],
                expected_answer=(
                    "Variable — if yes, undermines claim of no knowledge of Natalie"
                ),
                purpose_note=(
                    "If she admits recognition, locks knowledge of co-tenant Natalie "
                    "as of 2015. If she denies, consider handwriting / provenance follow-ups."
                ),
                tags=["natalie", "co_tenant", "handwriting", "EM-019"],
                follow_ups=[
                    "Who is Natalie?",
                    "When did you first learn Natalie lived in the unit?",
                    "Did you ever collect rent or correspondence naming Natalie?",
                ],
            ),
            ExaminationQuestion(
                question_id="Q4",
                purpose=QuestionPurpose.DOCUMENT,
                purpose_label="Nuisance property claim",
                text=(
                    "Counsel stated in the hearing that the property was 'deemed a nuisance "
                    "property since 2024.' Can you point to any document in the evidence that "
                    "establishes this designation?"
                ),
                source_transcript=TranscriptPin(
                    timestamp="37:00",
                    source_label="Transcript",
                ),
                expected_answer="Cannot produce — assertion without documentation",
                purpose_note=(
                    "Show arbitrator accepted unproven assertion; force documentary foundation "
                    "for 'nuisance property' / 400-calls narrative."
                ),
                tags=["nuisance", "400_calls", "foundation", "assertion"],
                follow_ups=[
                    "Who deemed it a nuisance property?",
                    "Is there a municipal order, RCMP designation, or written finding?",
                    "Are you relying only on counsel's statement?",
                ],
            ),
        ],
        notes=(
            "Planning outline only. Confirm Q1–Q4 wording against transcript audio. "
            "Link EM-019 to sequential EvidenceNode (EV-…) in the matter matrix before hearing. "
            "Do not invent answers; expected answers are strategic assumptions."
        ),
    )
