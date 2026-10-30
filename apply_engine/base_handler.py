"""
apply_engine/base_handler.py

Abstract base class for all application handlers.
Each concrete handler (LinkedIn, Generic, etc.) extends this.

SAFETY RULES encoded here:
- Never submits without explicit user confirmation.
- Never bypasses CAPTCHA, OTP, or auth challenges.
- Pauses and sets status to MANUAL_NEEDED when it hits a blocker.
- Never marks a job Applied unless submission is confirmed.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from apply_engine.apply_session import ApplySession
from apply_history import AppStatus


class BaseApplicationHandler(ABC):
    """Abstract base for all job site handlers."""

    HANDLER_NAME = "base"
    SUPPORTED_DOMAINS: list[str] = []  # Override in subclass

    def __init__(self, session: ApplySession, profile: dict):
        self.session = session
        self.profile = profile
        self.page: Page = None
        self.browser: Browser = None
        self.context: BrowserContext = None

    # ------------------------------------------------------------------ #
    #  Main entry point — called by the FastAPI task                       #
    # ------------------------------------------------------------------ #
    async def run(self):
        """
        Execute the full application flow.
        This method must NOT raise — it catches all errors and records them.
        """
        try:
            async with async_playwright() as pw:
                # Launch a visible (headed) browser so user can watch & intervene
                self.browser = await pw.chromium.launch(
                    headless=False,
                    args=["--start-maximized"]
                )
                self.context = await self.browser.new_context(
                    accept_downloads=True,
                    viewport=None  # Respects --start-maximized
                )
                self.page = await self.context.new_page()

                # Open the job URL
                self.session.set_status(
                    AppStatus.OPENING,
                    f"Opening application URL for {self.session.company}…"
                )
                await self._navigate(self.session.apply_url)

                # Detect form
                self.session.set_status(
                    AppStatus.DETECTING,
                    "Detecting application form…"
                )
                supported = await self.detect_form()

                if not supported:
                    self.session.set_status(
                        AppStatus.MANUAL_NEEDED,
                        "Automated form filling is not available for this site. "
                        "Please complete the application manually in the browser window."
                    )
                    # Keep browser open for manual completion
                    await self._wait_for_manual_close()
                    return

                # Fill form
                self.session.set_status(
                    AppStatus.FILLING,
                    "Filling application form fields…"
                )
                await self.fill_form()

                # Upload resume if needed
                resume_path = Path(self.profile.get("resume_path", ""))
                if resume_path.exists():
                    self.session.set_status(
                        AppStatus.UPLOADING,
                        "Uploading resume…"
                    )
                    await self.upload_resume(str(resume_path))

                # Pause for user review — MANDATORY
                self.session.set_status(
                    AppStatus.WAITING,
                    "✋ Review the filled application in the browser window. "
                    "Click 'Confirm & Submit' in the dashboard when ready, "
                    "or 'Abort' to cancel."
                )

                decision = await self.session.wait_for_user_decision(timeout_seconds=600)

                if decision == "confirmed":
                    await self.submit()
                    self.session.set_status(
                        AppStatus.SUBMITTED,
                        f"✅ Application submitted successfully to {self.session.company}!",
                        confirmation=f"Submitted at {self._now()}"
                    )
                elif decision == "aborted":
                    self.session.set_status(
                        AppStatus.ABORTED,
                        "Application aborted by user. No submission was made."
                    )
                else:
                    self.session.set_status(
                        AppStatus.ABORTED,
                        "Review window timed out (10 min). Application not submitted."
                    )

        except Exception as exc:
            error_msg = str(exc)
            self.session.set_status(
                AppStatus.FAILED,
                f"Error during application: {error_msg[:120]}",
                error=error_msg
            )
        finally:
            if self.browser:
                try:
                    await asyncio.sleep(3)  # Brief pause before closing
                    await self.browser.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    #  Abstract methods — must be implemented per site                     #
    # ------------------------------------------------------------------ #
    @abstractmethod
    async def detect_form(self) -> bool:
        """
        Return True if this handler can fill the form on the current page.
        Return False to fall back to manual mode.
        """
        ...

    @abstractmethod
    async def fill_form(self):
        """Fill known form fields using self.profile data."""
        ...

    @abstractmethod
    async def upload_resume(self, resume_path: str):
        """Handle resume file upload."""
        ...

    @abstractmethod
    async def submit(self):
        """
        Execute final form submission.
        Only called AFTER user explicit confirmation.
        """
        ...

    # ------------------------------------------------------------------ #
    #  Shared helpers                                                      #
    # ------------------------------------------------------------------ #
    async def _navigate(self, url: str, timeout: int = 30000):
        await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        await asyncio.sleep(2)  # Brief settle time

    async def _try_fill_field(self, selector: str, value: str, label: str = ""):
        """Safely attempt to fill a field — logs warning if not found."""
        try:
            el = await self.page.query_selector(selector)
            if el:
                await el.fill(value)
                return True
        except Exception as e:
            print(f"[handler] Could not fill '{label}' ({selector}): {e}")
        return False

    async def _try_upload_file(self, selector: str, file_path: str) -> bool:
        """Safely attempt to set a file input."""
        try:
            el = await self.page.query_selector(selector)
            if el:
                await el.set_input_files(file_path)
                return True
        except Exception as e:
            print(f"[handler] Could not upload file via '{selector}': {e}")
        return False

    async def _check_for_captcha(self) -> bool:
        """Detect common CAPTCHA signals — never bypass, just report."""
        captcha_signals = [
            "iframe[src*='recaptcha']",
            "iframe[src*='hcaptcha']",
            ".g-recaptcha",
            "[data-sitekey]",
            "iframe[title*='challenge']"
        ]
        for sel in captcha_signals:
            el = await self.page.query_selector(sel)
            if el:
                self.session.set_status(
                    AppStatus.MANUAL_NEEDED,
                    "🔒 CAPTCHA detected. Please solve it manually in the browser window, "
                    "then click 'Confirm & Submit' in the dashboard."
                )
                return True
        return False

    async def _wait_for_manual_close(self, timeout_seconds: int = 600):
        """Keep session open waiting for user decision while browser is open."""
        decision = await self.session.wait_for_user_decision(timeout_seconds)
        if decision == "aborted":
            self.session.set_status(AppStatus.ABORTED, "Aborted by user.")

    @staticmethod
    def _now() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def matches_url(url: str, domains: list[str]) -> bool:
        url_lower = url.lower()
        return any(d in url_lower for d in domains)

