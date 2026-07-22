"""Process-local engines for Phase 3–4 / 4-4 (in-memory until Postgres)."""

from __future__ import annotations

from services.post_resolution.service import PostResolutionEngine
from services.reasoning.hitl.control_plane.service import HitlControlPlane

# Singletons for demo API — production replaces with DB-backed services
hitl = HitlControlPlane()
post_resolution = PostResolutionEngine()
