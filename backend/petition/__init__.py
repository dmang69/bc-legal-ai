"""Petition outline persistence."""

from architecture.petition import (
    PetitionCite,
    PetitionGround,
    PetitionOutline,
    PetitionSubGround,
    PredictedOpposition,
    RiskLevel,
)
from backend.petition.service import list_petitions, load_petition, save_petition
from templates.petition.rtb_jr_petition_outline import rtb_jr_petition_outline

__all__ = [
    "PetitionCite",
    "PetitionGround",
    "PetitionOutline",
    "PetitionSubGround",
    "PredictedOpposition",
    "RiskLevel",
    "list_petitions",
    "load_petition",
    "save_petition",
    "rtb_jr_petition_outline",
]
