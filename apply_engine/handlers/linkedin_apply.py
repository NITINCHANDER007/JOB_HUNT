"""
apply_engine/handlers/linkedin_apply.py

Dedicated LinkedIn Easy Apply Automation Handler.
Uses authenticated LinkedIn browser sessions, automatically fills Easy Apply modals,
attaches resume, checks for security challenges/CAPTCHAs, pauses for human verification,
and enforces safety confirmation before final submission.
"""

import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Page, BrowserContext

from apply_engine.base_handler import BaseApplicationHandler
from apply_engine.smart_form_filler import SmartFormFiller
from apply_engine.captcha_detector import CaptchaDetector
from apply_engine.browser_session_manager import session_manager
from apply_history import AppStatus


class LinkedInApplyHandler(BaseApplicationHandler):
    """Automates applications on LinkedIn (Easy Apply & company portal handoff)."""

    HANDLER_NAME = "linkedin_easy_apply"
    SUPPORTED_DOMAINS = ["linkedin.com"]

    def __init__(self, session, profile):
        super().__init__(session, profile)
        self.filler: Optional[SmartFormFiller] = None
        self.captcha: Optional[CaptchaDetector] = None

    async def run(self):
        """Execute the LinkedIn application lifecycle."""
        try:
            async with async_playwright() as pw:
                # 1. Load authenticated session if available
                self.context = await session_manager.get_authenticated_context(
                    pw,
                    platform="linkedin",
                    headless=False
                )
                self.page = await self.context.new_page()
                self.captcha = CaptchaDetector(self.page, self.session)
                self.filler = SmartFormFiller(self.page, self.profile)

                # 2. Navigate to job URL
                self.session.set_status(
                    AppStatus.OPENING,
                    f"Navigating to LinkedIn job for {self.session.company}…"
                )
                await self._navigate(self.session.apply_url)

                # 3. Check for login / security verification
                is_resolved = await self.captcha.handle_challenge_if_present()
                if not is_resolved:
                    return

                # Check if logged in or prompted for login
                login_btn = await self.page.query_selector("a[href*='login'], button:has-text('Sign in')")
                if login_btn and await login_btn.is_visible():
                    self.session.set_status(
                        AppStatus.MANUAL_NEEDED,
                        "⚠️ Please sign in to LinkedIn in the browser window to continue with automated application."
                    )
                    # Wait for user to log in or abort
                    await self._wait_for_login(timeout_seconds=120)

                # 4. Detect application type (Easy Apply vs External)
                self.session.set_status(AppStatus.DETECTING, "Detecting LinkedIn application type…")
                await asyncio.sleep(2)

                easy_apply_btn = await self._find_easy_apply_button()

                if not easy_apply_btn:
                    # Check if there is an external "Apply" button
                    external_apply = await self.page.query_selector("button:has-text('Apply'), a:has-text('Apply')")
                    if external_apply:
                        self.session.set_status(
                            AppStatus.MANUAL_NEEDED,
                            "External company application required. Opening destination career site…"
                        )
                        await external_apply.click()
                        await asyncio.sleep(4)
                        # Switch to new page if opened in tab
                        pages = self.context.pages
                        if len(pages) > 1:
                            self.page = pages[-1]
                            self.filler = SmartFormFiller(self.page, self.profile)
                            self.captcha = CaptchaDetector(self.page, self.session)
                            # Delegate to smart form filler on target page
                            await self._fill_and_submit_portal()
                            return

                    self.session.set_status(
                        AppStatus.MANUAL_NEEDED,
                        "Could not locate an active Easy Apply button. Please complete manually in the open window."
                    )
                    await self._wait_for_manual_close()
                    return

                # 5. Click Easy Apply and step through modal
                self.session.set_status(AppStatus.FILLING, "Opening LinkedIn Easy Apply modal…")
                await easy_apply_btn.click()
                await asyncio.sleep(2)

                # Step through modal steps
                completed_flow = await self._process_easy_apply_modal()

                if not completed_flow:
                    return

                # 6. Capture review screenshot
                screenshot_path = await self.filler.capture_audit_screenshot(
                    self.session.company,
                    self.session.job_id
                )

                # 7. Pause for user review — MANDATORY SAFETY RULE
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
                        f"✅ Application submitted successfully to {self.session.company} on LinkedIn!",
                        confirmation=f"LinkedIn Easy Apply submitted at {self._now()}"
                    )
                elif decision == "aborted":
                    self.session.set_status(
                        AppStatus.ABORTED,
                        "Application aborted by user. No submission was made."
                    )
                else:
                    self.session.set_status(
                        AppStatus.ABORTED,
                        "Review window timed out. Application not submitted."
                    )

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
        btn = await self._find_easy_apply_button()
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
        """Click the final Submit application button inside LinkedIn modal."""
        submit_selectors = [
            "button[aria-label='Submit application']",
            "button:has-text('Submit application')",
            "footer button:has-text('Submit')"
        ]
        for sel in submit_selectors:
            btn = await self.page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                await asyncio.sleep(3)
                # Check for dismiss / done button
                done_btn = await self.page.query_selector("button:has-text('Done'), button[aria-label='Dismiss']")
                if done_btn:
                    await done_btn.click()
                return

    # ── Internal Helpers ─────────────────────────────────────────────────── #

    async def _find_easy_apply_button(self):
        """Locate the Easy Apply button on the LinkedIn job details page."""
        selectors = [
            ".jobs-apply-button",
            "button[aria-label*='Easy Apply']",
            "button:has-text('Easy Apply')",
            ".jobs-s-apply button"
        ]
        for sel in selectors:
            btn = await self.page.query_selector(sel)
            if btn and await btn.is_visible():
                return btn
        return None

    async def _process_easy_apply_modal(self) -> bool:
        """Walk through LinkedIn Easy Apply dialog steps (Contact, Resume, Questions, Review)."""
        max_steps = 8
        step = 0

        while step < max_steps:
            step += 1
            await asyncio.sleep(1.5)

            # Check challenge / CAPTCHA
            if not await self.captcha.handle_challenge_if_present():
                return False

            # Fill available fields on current step
            await self.fill_form()

            # Upload resume if file input is present
            resume_path = self.profile.get("resume_path", "")
            if resume_path and Path(resume_path).exists():
                await self.upload_resume(str(resume_path))

            # Check if we've reached the final Review step
            review_btn = await self.page.query_selector("button:has-text('Review')")
            submit_btn = await self.page.query_selector(
                "button[aria-label='Submit application'], button:has-text('Submit application')"
            )

            if submit_btn and await submit_btn.is_visible():
                # Ready for user review!
                return True

            if review_btn and await review_btn.is_visible():
                await review_btn.click()
                await asyncio.sleep(1.5)
                return True

            # Look for "Next" button
            next_btn = await self.page.query_selector("button[aria-label='Continue to next step'], button:has-text('Next')")
            if next_btn and await next_btn.is_visible():
                # Check for any required question that wasn't answered
                unanswered = await self.filler.detect_unanswered_required_fields()
                if unanswered:
                    q_text = unanswered[0].get("question", "Required screening question")
                    self.session.set_status(
                        AppStatus.MANUAL_NEEDED,
                        f"❓ Question requires input: '{q_text}'. Please answer in the open window."
                    )
                    # Wait briefly for user to fill or click Next
                    await asyncio.sleep(3)

                await next_btn.click()
                await asyncio.sleep(1.5)
            else:
                break

        return True

    async def _fill_and_submit_portal(self):
        """Helper to fill external career portal if redirected."""
        await asyncio.sleep(2)
        await self.filler.auto_fill(company=self.session.company, role=self.session.role)
        resume_path = self.profile.get("resume_path", "")
        if resume_path and Path(resume_path).exists():
            await self.upload_resume(str(resume_path))

        self.session.set_status(
            AppStatus.WAITING,
            "✋ External career form filled. Please review and click 'Confirm & Submit'."
        )
        decision = await self.session.wait_for_user_decision(timeout_seconds=600)
        if decision == "confirmed":
            # Click submit button
            for sel in ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Submit")']:
                b = await self.page.query_selector(sel)
                if b and await b.is_visible():
                    await b.click()
                    break
            self.session.set_status(
                AppStatus.SUBMITTED,
                f"✅ Application submitted successfully to {self.session.company}!",
                confirmation=f"External portal submission at {self._now()}"
            )

    async def _wait_for_login(self, timeout_seconds: int = 120):
        """Wait for human login completion in the browser."""
        start = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start) < timeout_seconds:
            login_el = await self.page.query_selector("a[href*='login'], button:has-text('Sign in')")
            if not login_el or not await login_el.is_visible():
                # Logged in! Save session
                state_file = session_manager.get_state_file("linkedin")
                try:
                    await self.context.storage_state(path=str(state_file))
                except Exception:
                    pass
                self.session.set_status(AppStatus.OPENING, "LinkedIn login detected! Proceeding…")
                return True
            await asyncio.sleep(2)
        return False
