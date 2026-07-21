"""Case status dashboard."""

from architecture.case_status import CaseDashboard
from backend.dashboard.service import load_dashboard, save_dashboard
from templates.case.kam_s_s_65285_dashboard import kam_s_s_65285_dashboard

__all__ = [
    "CaseDashboard",
    "kam_s_s_65285_dashboard",
    "load_dashboard",
    "save_dashboard",
]
