"""
apply_engine/handler_registry.py

Router that selects the appropriate handler for a given application URL.
Add new handlers here as support for more sites is built.
"""

from apply_engine.apply_session import ApplySession
from apply_engine.base_handler import BaseApplicationHandler
from apply_engine.handlers.demo_form import DemoFormHandler
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

    # Future: LinkedIn Easy Apply
    # if "linkedin.com" in url_lower:
    #     from apply_engine.handlers.linkedin import LinkedInHandler
    #     return LinkedInHandler(session=session, profile=profile)

    # Future: Keka career portal
    # if "keka.com" in url_lower:
    #     from apply_engine.handlers.keka import KekaHandler
    #     return KekaHandler(session=session, profile=profile)

    # Default: open the link and let the user apply manually
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
            "site": "LinkedIn Jobs",
            "domains": ["linkedin.com"],
            "automation": "Planned — opens link, manual application required for now",
            "status": "🔜 Manual only (Easy Apply handler coming soon)"
        },
        {
            "site": "Keka Career Portal",
            "domains": ["keka.com"],
            "automation": "Opens link — manual application",
            "status": "🔜 Manual only"
        },
        {
            "site": "All other sites",
            "domains": ["*"],
            "automation": "Opens link in browser — user completes manually",
            "status": "⚠️ Manual only — automated filling not available"
        },
    ]

