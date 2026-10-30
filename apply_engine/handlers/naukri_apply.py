"""
apply_engine/handlers/naukri_apply.py

Dedicated Naukri.com Application Handler.
Uses authenticated Naukri browser sessions, detects Apply on Naukri buttons,
handles chatbot / question dialogs, attaches resume, monitors OTP/CAPTCHA,
and pauses for human verification and safety confirmation.
"""

import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright

from apply_engine.base_handler import BaseApplicationHandler
from apply_engine.smart_form_filler import SmartFormFiller
from apply_engine.captcha_detector import CaptchaDetector
from apply_engine.browser_session_manager import session_manager
from apply_history import AppStatus


class NaukriApplyHandler(BaseApplicationHandler):
    """Automates applications on Naukri.com."""

    HANDLER_NAME = "naukri_apply"
    SUPPORTED_DOMAINS = ["naukri.com"]

    def __init__(self, session, profile):
        super().__init__(session, profile)
        self.filler: Optional[SmartFormFiller] = None
        self.captcha: Optional[CaptchaDetector] = None

    async def run(self):
        try:
            async with async_playwright() as pw:
                self.context = await session_manager.get_authenticated_context(
                    pw,
                    platform="naukri",
                    headless=False
                )
                self.page = await self.context.new_page()
                self.captcha = CaptchaDetector(self.page, self.session)
                self.filler = SmartFormFiller(self.page, self.profile)

                self.session.set_status(
                    AppStatus.OPENING,
                    f"Navigating to Naukri job for {self.session.company}…"
                )
                await self._navigate(self.session.apply_url)

                # Check security challenge
                if not await self.captcha.handle_challenge_if_present():
                    return

                # Check login
                login_btn = await self.page.query_selector("a#login_Layer, .nI-gNb-header__login-btn")
                if login_btn and await login_btn.is_visible():
                    self.session.set_status(
                        AppStatus.MANUAL_NEEDED,
                        "⚠️ Please sign in to Naukri in the browser window to continue with automated application."
                    )
                    await self._wait_for_login(timeout_seconds=120)

                # Locate Apply button
                self.session.set_status(AppStatus.DETECTING, "Detecting Naukri apply button…")
                await asyncio.sleep(2)

                apply_btn = await self._find_apply_button()
                if not apply_btn:
                    self.session.set_status(
                        AppStatus.MANUAL_NEEDED,
                        "Could not locate active apply button on Naukri. Please complete manually in the browser window."
                    )
                    await self._wait_for_manual_close()
                    return

                # Click apply
                self.session.set_status(AppStatus.FILLING, "Triggering application on Naukri…")
                await apply_btn.click()
                await asyncio.sleep(2)

                # Handle questionnaire or screening modal if present
                await self.filler.auto_fill(company=self.session.company, role=self.session.role)
                resume_path = self.profile.get("resume_path", "")
                if resume_path and Path(resume_path).exists():
                    await self.upload_resume(str(resume_path))

                # Capture audit screenshot
                await self.filler.capture_audit_screenshot(self.session.company, self.session.job_id)

                # Pause for user review
                self.session.set_status(
                    AppStatus.WAITING,
                    "✋ Review your filled application in the browser window. "
                    "Click 'Confirm & Submit' in the dashboard to submit, or 'Abort' to cancel."
                )

                decision = await self.session.wait_for_user_decision(timeout_seconds=600)
                if decision == "confirmed":
                    await self.submit()
                    self.session.set_status(
                        AppStatus.SUBMITTED,
                        f"✅ Application submitted successfully to {self.session.company} on Naukri!",
                        confirmation=f"Naukri application submitted at {self._now()}"
                    )
                elif decision == "aborted":
                    self.session.set_status(AppStatus.ABORTED, "Application aborted by user.")
                else:
                    self.session.set_status(AppStatus.ABORTED, "Review window timed out.")

        except Exception as exc:
            err = str(exc)
            self.session.set_status(
                AppStatus.FAILED,
                f"Error during application: {err[:120]}",
                error=err
            )
        finally:
            if self.context:
                try:
                    await asyncio.sleep(2)
                    await self.context.close()
                except Exception:
                    pass

    async def detect_form(self) -> bool:
        btn = await self._find_apply_button()
        return btn is not None

    async def fill_form(self):
        if not self.filler:
            self.filler = SmartFormFiller(self.page, self.profile)
        await self.filler.auto_fill(company=self.session.company, role=self.session.role)

    async def upload_resume(self, resume_path: str):
        if not self.filler:
            self.filler = SmartFormFiller(self.page, self.profile)
        await self.filler.upload_resume(resume_path)

    async def submit(self):
        """Submit the application on Naukri."""
        for sel in [
            "button.apply-button",
            "button:has-text('Submit')",
            "button:has-text('Save and Apply')",
            "#apply-button"
        ]:
            b = await self.page.query_selector(sel)
            if b and await b.is_visible():
                await b.click()
                await asyncio.sleep(2)
                return

    async def _find_apply_button(self):
        selectors = [
            "button.apply-button",
            "#apply-button",
            "button:has-text('Apply')",
            ".apply-button-container button"
        ]
        for sel in selectors:
            btn = await self.page.query_selector(sel)
            if btn and await btn.is_visible():
                return btn
        return None

    async def _wait_for_login(self, timeout_seconds: int = 120):
        start = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start) < timeout_seconds:
            login_el = await self.page.query_selector("a#login_Layer, .nI-gNb-header__login-btn")
            if not login_el or not await login_el.is_visible():
                state_file = session_manager.get_state_file("naukri")
                try:
                    await self.context.storage_state(path=str(state_file))
                except Exception:
                    pass
                self.session.set_status(AppStatus.OPENING, "Naukri login detected! Proceeding…")
                return True
            await asyncio.sleep(2)
        return False
