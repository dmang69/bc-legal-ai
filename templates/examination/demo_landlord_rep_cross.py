"""
SYNTHETIC cross-examination outline — fictional witness only.

No real party names. Structure only for workbench tests.
"""

from __future__ import annotations

from architecture.examination import (
    ExaminationOutline,
    ExaminationQuestion,
    QuestionPurpose,
    TranscriptPin,
)


def demo_landlord_rep_cross(*, matter_id: str | None = None) -> ExaminationOutline:
    return ExaminationOutline(
        outline_id="EXAM-CROSS-DEMO-001",
        title="[SYNTHETIC] CROSS OF LANDLORD'S REPRESENTATIVE",
        target_witness="[SYNTHETIC] Alex Manager",
        goal=(
            "[SYNTHETIC] Establish agency role and knowledge of co-occupant; "
            "test attribution of alleged service calls (demo structure only)"
        ),
        exam_type="CROSS",
        matter_id=matter_id,
        related_legal_tests=[],  # no disabled s.56 retaliation test
        questions=[
            ExaminationQuestion(
                question_id="Q1",
                purpose=QuestionPurpose.FOUNDATIONAL,
                purpose_label="Foundational — establish role",
                text=(
                    "You manage the rental property on behalf of the owner, correct?"
                ),
                source_transcript=TranscriptPin(
                    timestamp="00:00",
                    source_label="[SYNTHETIC] Transcript placeholder",
                ),
                expected_answer="Yes",
                tags=["management", "agency", "foundational", "synthetic"],
            ),
            ExaminationQuestion(
                question_id="Q2",
                purpose=QuestionPurpose.LOCK_IN,
                purpose_label="Knowledge of occupants",
                text="You were aware another adult occupied the unit with the tenant?",
                source_transcript=TranscriptPin(
                    timestamp="00:00",
                    source_label="[SYNTHETIC] Transcript placeholder",
                ),
                expected_answer="[planning assumption only]",
                tags=["occupants", "synthetic"],
            ),
        ],
        notes=(
            "SYNTHETIC DEMO ONLY. Do not use against real witnesses. "
            "Verify any real transcript pins before hearing use."
        ),
    )


def sanghera_cross_outline(*, matter_id: str | None = None) -> ExaminationOutline:
    """Deprecated alias — returns synthetic outline."""
    return demo_landlord_rep_cross(matter_id=matter_id)
