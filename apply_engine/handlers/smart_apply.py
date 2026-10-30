"""
apply_engine/handlers/smart_apply.py
Universal Smart Application Handler for Career Portals and ATS Forms.
Extends BaseApplicationHandler to automate form detection, population,
resume upload, cover note generation, CAPTCHA/challenge monitoring, and submission.
"""

from pathlib import Path
from apply_engine.base_handler import BaseApplicationHandler
from apply_engine.smart_form_filler import SmartFormFiller
from apply_engine.captcha_detector import CaptchaDetector
from apply_history import AppStatus


class SmartApplyHandler(BaseApplicationHandler):
    """Universal AI-assisted handler for modern job boards and ATS forms."""

    HANDLER_NAME = "smart_apply"
    SUPPORTED_DOMAINS = [
        "greenhouse.io",
        "lever.co",
        "ashbyhq.com",
        "workday.com",
        "smartrecruiters.com",
        "breezy.hr",
        "keka.com",
        "workable.com"
    ]

    def __init__(self, session, profile):
        super().__init__(session, profile)
        self.filler: SmartFormFiller = None
        self.captcha: CaptchaDetector = None

    async def detect_form(self) -> bool:
        """Detect whether a job application form is present on the page."""
        try:
            self.captcha = CaptchaDetector(self.page, self.session)
            # Check for security challenge first
            if not await self.captcha.handle_challenge_if_present():
                return False

            # Check for form tag or input elements
            inputs = await self.page.query_selector_all("form, input:not([type='hidden']), textarea")
            if len(inputs) >= 3:
                self.filler = SmartFormFiller(self.page, self.profile)
                return True
        except Exception:
            pass
        return False

    async def fill_form(self):
        """Intelligently fill form fields using candidate profile."""
        if not self.filler:
            self.filler = SmartFormFiller(self.page, self.profile)

        # Monitor CAPTCHA/OTP before filling
        if self.captcha:
            await self.captcha.handle_challenge_if_present()

        res = await self.filler.auto_fill(
            company=self.session.company,
            role=self.session.role
        )
        filled_count = res.get("filled_count", 0)
        unanswered = res.get("unanswered_required", [])

        # Capture audit screenshot
        screenshot_path = await self.filler.capture_audit_screenshot(
            self.session.company,
            self.session.job_id
        )

        msg = f"Populated {filled_count} fields automatically. Screenshot captured for review."
        if unanswered:
            msg += f" (Note: {len(unanswered)} optional/custom question(s) may need your review)."

        self.session.set_status(AppStatus.FILLING, msg)

    async def upload_resume(self, resume_path: str):
        """Upload candidate resume to file input."""
        if not self.filler:
            self.filler = SmartFormFiller(self.page, self.profile)

        uploaded = await self.filler.upload_resume(resume_path)
        if uploaded:
            self.session.set_status(
                AppStatus.UPLOADING,
                "✅ Resume file attached successfully."
            )

    async def submit(self):
        """Submit the application form upon explicit user confirmation."""
        # Find submit button
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit Application")',
            'button:has-text("Apply Now")',
            'button:has-text("Submit")'
        ]
        for sel in submit_selectors:
            btn = await self.page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                await self.page.wait_for_timeout(3000)
                return
