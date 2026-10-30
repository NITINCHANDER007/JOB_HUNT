"""
apply_engine/handlers/generic.py

Fallback handler for unsupported job application websites.

Behaviour:
- Opens the application URL in a visible browser.
- Informs the user that automated form filling is unavailable.
- Keeps the browser open for manual completion.
- Never pretends to have submitted.
"""

from apply_engine.base_handler import BaseApplicationHandler
from apply_engine.apply_session import ApplySession
from apply_history import AppStatus


class GenericHandler(BaseApplicationHandler):
    """Fallback for unsupported sites — manual flow only."""

    HANDLER_NAME = "generic"
    SUPPORTED_DOMAINS = []  # Matches everything as fallback

    async def detect_form(self) -> bool:
        # Generic handler always returns False — triggers manual mode
        return False

    async def fill_form(self):
        # Never called for generic handler
        pass

    async def upload_resume(self, resume_path: str):
        # Never called for generic handler
        pass

    async def submit(self):
        # Never called for generic handler
        pass

