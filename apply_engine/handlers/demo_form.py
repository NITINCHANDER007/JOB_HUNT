"""
apply_engine/handlers/demo_form.py

Handler for the local test form (test_form.html).
This is the ONLY handler that actually fills and submits a form in tests.
Used exclusively for safe local testing — never against real employers.
"""

from apply_engine.base_handler import BaseApplicationHandler
from apply_history import AppStatus


class DemoFormHandler(BaseApplicationHandler):
    """Handler for the local test_form.html — used for safe testing only."""

    HANDLER_NAME = "demo_form"
    SUPPORTED_DOMAINS = ["localhost", "127.0.0.1"]

    async def detect_form(self) -> bool:
        """Detect the demo form."""
        try:
            form = await self.page.query_selector("form#demo-apply-form")
            return form is not None
        except Exception:
            return False

    async def fill_form(self):
        """Fill all standard fields in the demo test form."""
        p = self.profile

        await self._try_fill_field('input[name="full_name"]',
                                   p.get("full_name", ""), "Full Name")
        await self._try_fill_field('input[name="email"]',
                                   p.get("email", ""), "Email")
        await self._try_fill_field('input[name="phone"]',
                                   p.get("phone", ""), "Phone")
        await self._try_fill_field('input[name="college"]',
                                   p.get("college", ""), "College")
        await self._try_fill_field('input[name="degree"]',
                                   p.get("degree", ""), "Degree")
        await self._try_fill_field('input[name="graduation_year"]',
                                   p.get("graduation_year", ""), "Graduation Year")
        await self._try_fill_field('input[name="cgpa"]',
                                   p.get("cgpa", ""), "CGPA")
        await self._try_fill_field('input[name="linkedin"]',
                                   p.get("linkedin", ""), "LinkedIn")
        await self._try_fill_field('input[name="github"]',
                                   p.get("github", ""), "GitHub")

        # Skills as comma-separated list
        skills = ", ".join(p.get("skills", []))
        await self._try_fill_field('textarea[name="skills"]', skills, "Skills")
        await self._try_fill_field('input[name="skills"]', skills, "Skills (input)")

    async def upload_resume(self, resume_path: str):
        """Upload resume to the demo form file input."""
        success = await self._try_upload_file('input[type="file"]', resume_path)
        if not success:
            # Try named input
            success = await self._try_upload_file('input[name="resume"]', resume_path)
        if success:
            self.session.set_status(
                "Resume uploaded",
                "✅ Resume file selected for upload."
            )

    async def submit(self):
        """Submit the demo form — safe local form only."""
        try:
            submit_btn = await self.page.query_selector(
                'button[type="submit"], input[type="submit"]'
            )
            if submit_btn:
                await submit_btn.click()
                # Wait for confirmation message
                await self.page.wait_for_selector(
                    "#submission-success, .success-message, #submit-result",
                    timeout=5000
                )
        except Exception as e:
            raise RuntimeError(f"Form submission failed: {e}")

