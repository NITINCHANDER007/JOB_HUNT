"""
apply_engine/handler_registry.py

Router that selects the appropriate handler for a given application URL.
Add new handlers here as support for more sites is built.
"""

from apply_engine.apply_session import ApplySession
from apply_engine.base_handler import BaseApplicationHandler
from apply_engine.handlers.demo_form import DemoFormHandler
from apply_engine.handlers.smart_apply import SmartApplyHandler
from apply_engine.handlers.generic import GenericHandler


def get_handler(apply_url: str, session: ApplySession, profile: dict) -> BaseApplicationHandler:
    """
    Return the best available handler for the given URL.
    Falls back to GenericHandler (manual mode) if no specific handler matches.
    """
    url_lower = apply_url.lower()

    # Demo / test form (localhost)
    if "localhost" in url_lower or "127.0.0.1" in url_lower:
        return DemoFormHandler(session=session, profile=profile)

    # ATS and Career Portals (Smart Form Filler)
    for domain in SmartApplyHandler.SUPPORTED_DOMAINS:
        if domain in url_lower:
            return SmartApplyHandler(session=session, profile=profile)

    # Default: open the link and let the user apply manually (includes LinkedIn, Indeed, Naukri)
    return GenericHandler(session=session, profile=profile)


def list_supported_sites() -> list[dict]:
    """Return info about what's currently supported."""
    return [
        {
            "site": "Local Demo Form (test_form.html)",
            "domains": ["localhost", "127.0.0.1"],
            "automation": "Full — fills all fields, uploads resume, confirms before submit",
            "status": "✅ Supported"
        },
        {
            "site": "ATS Career Portals (Greenhouse, Lever, Ashby, Workday, Breezy)",
            "domains": SmartApplyHandler.SUPPORTED_DOMAINS,
            "automation": "Smart AI Form Filler — auto-detects fields, uploads resume, captures audit screenshots",
            "status": "✅ Supported"
        },
        {
            "site": "LinkedIn Jobs",
            "domains": ["linkedin.com"],
            "automation": "Planned — opens link, manual application required for now",
            "status": "🔜 Manual only (Easy Apply handler coming soon)"
        },
        {
            "site": "All other sites",
            "domains": ["*"],
            "automation": "Opens link in browser — user completes manually",
            "status": "⚠️ Manual only — automated filling not available"
        },
    ]

