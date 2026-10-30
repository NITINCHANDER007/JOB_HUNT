"""
apply_engine/handler_registry.py

Router that selects the appropriate handler for a given application URL.
Supports:
- Local Demo Test Form (localhost, 127.0.0.1)
- LinkedIn Easy Apply (linkedin.com)
- Naukri.com (naukri.com)
- Indeed.com (indeed.com)
- ATS & Career Portals (Greenhouse, Lever, Ashby, Workday, Breezy, Workable, etc.)
- Generic fallback
"""

from apply_engine.apply_session import ApplySession
from apply_engine.base_handler import BaseApplicationHandler
from apply_engine.handlers.demo_form import DemoFormHandler
from apply_engine.handlers.smart_apply import SmartApplyHandler
from apply_engine.handlers.linkedin_apply import LinkedInApplyHandler
from apply_engine.handlers.naukri_apply import NaukriApplyHandler
from apply_engine.handlers.indeed_apply import IndeedApplyHandler
from apply_engine.handlers.generic import GenericHandler


def get_handler(apply_url: str, session: ApplySession, profile: dict) -> BaseApplicationHandler:
    """
    Return the best available handler for the given URL.
    """
    url_lower = apply_url.lower()

    # 1. Demo / test form (localhost)
    if "localhost" in url_lower or "127.0.0.1" in url_lower:
        return DemoFormHandler(session=session, profile=profile)

    # 2. LinkedIn Jobs & Easy Apply
    if "linkedin.com" in url_lower:
        return LinkedInApplyHandler(session=session, profile=profile)

    # 3. Naukri Jobs
    if "naukri.com" in url_lower:
        return NaukriApplyHandler(session=session, profile=profile)

    # 4. Indeed Jobs
    if "indeed.com" in url_lower:
        return IndeedApplyHandler(session=session, profile=profile)

    # 5. ATS and Career Portals (Smart Form Filler)
    for domain in SmartApplyHandler.SUPPORTED_DOMAINS:
        if domain in url_lower:
            return SmartApplyHandler(session=session, profile=profile)

    # 6. Fallback: Smart Apply handles any web form, with Generic fallback
    return SmartApplyHandler(session=session, profile=profile)


def list_supported_sites() -> list[dict]:
    """Return info about all supported platforms and automations."""
    return [
        {
            "site": "Local Demo Form (test_form.html)",
            "domains": ["localhost", "127.0.0.1"],
            "automation": "Full — fills all fields, uploads resume, confirms before submit",
            "status": "✅ Fully Supported"
        },
        {
            "site": "LinkedIn Easy Apply",
            "domains": ["linkedin.com"],
            "automation": "Full — Authenticated session, modal stepper, question answering, CAPTCHA detection, resume upload",
            "status": "✅ Fully Supported"
        },
        {
            "site": "Naukri.com",
            "domains": ["naukri.com"],
            "automation": "Full — Authenticated session, 1-click & question dialogs, OTP monitoring, resume attach",
            "status": "✅ Fully Supported"
        },
        {
            "site": "Indeed.com",
            "domains": ["indeed.com"],
            "automation": "Full — Authenticated session, multi-step Indeed Apply, Cloudflare & CAPTCHA detection",
            "status": "✅ Fully Supported"
        },
        {
            "site": "ATS Career Portals (Greenhouse, Lever, Ashby, Workday, Breezy, Workable)",
            "domains": SmartApplyHandler.SUPPORTED_DOMAINS,
            "automation": "Smart AI Form Filler — auto-detects fields, uploads resume & cover note, captures audit screenshots",
            "status": "✅ Fully Supported"
        },
        {
            "site": "Direct Company Career Portals",
            "domains": ["*"],
            "automation": "Smart Form Filler — heuristic semantic field matching, resume upload, safety review",
            "status": "✅ Supported"
        },
    ]
