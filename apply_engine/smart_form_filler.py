"""
apply_engine/smart_form_filler.py
Intelligent Form Filling Engine using Playwright.

Analyzes web application pages, identifies field semantics via labels,
placeholders, and ARIA attributes, and auto-fills candidate details
with resume upload support and screenshot auditing.
"""

import os
import re
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.async_api import Page, ElementHandle

BASE_DIR = Path(__file__).parent.parent
SCREENSHOT_DIR = BASE_DIR / "exports" / "apply_screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


class SmartFormFiller:
    """Intelligently detects and populates job application forms."""

    def __init__(self, page: Page, profile: Dict[str, Any]):
        self.page = page
        self.profile = profile

    async def auto_fill(self) -> Dict[str, Any]:
        """Inspect and fill all detectable fields on the page."""
        filled_fields = []

        # 1. Full name or First / Last Name
        full_name = self.profile.get("full_name", "")
        parts = full_name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        if await self._fill_first_matching(
            [r"full[-_ ]?name", r"^name$", r"candidate[-_ ]?name"],
            full_name
        ):
            filled_fields.append("full_name")
        else:
            if await self._fill_first_matching([r"first[-_ ]?name", r"fname", r"given[-_ ]?name"], first_name):
                filled_fields.append("first_name")
            if await self._fill_first_matching([r"last[-_ ]?name", r"lname", r"family[-_ ]?name", r"surname"], last_name):
                filled_fields.append("last_name")

        # 2. Email Address
        if await self._fill_first_matching([r"email", r"e[-_ ]?mail"], self.profile.get("email", "")):
            filled_fields.append("email")

        # 3. Phone Number
        if await self._fill_first_matching([r"phone", r"mobile", r"contact[-_ ]?number", r"tel"], self.profile.get("phone", "")):
            filled_fields.append("phone")

        # 4. College / University
        college = self.profile.get("college", "Maharaja Agrasen Institute of Technology (MAIT)")
        if await self._fill_first_matching([r"college", r"university", r"school", r"institution"], college):
            filled_fields.append("college")

        # 5. Degree / Major
        degree = self.profile.get("degree", "B.Tech in Computer Science")
        if await self._fill_first_matching([r"degree", r"major", r"field[-_ ]?of[-_ ]?study", r"course"], degree):
            filled_fields.append("degree")

        # 6. Graduation Year
        grad_year = str(self.profile.get("graduation_year", "2027"))
        if await self._fill_first_matching([r"graduat(?:ion|ed)[-_ ]?year", r"passing[-_ ]?year", r"yoe", r"batch"], grad_year):
            filled_fields.append("graduation_year")

        # 7. CGPA / Marks
        cgpa = str(self.profile.get("cgpa", "8.0"))
        if await self._fill_first_matching([r"cgpa", r"gpa", r"percentage", r"grade"], cgpa):
            filled_fields.append("cgpa")

        # 8. LinkedIn Profile
        linkedin = self.profile.get("linkedin", "")
        if linkedin and await self._fill_first_matching([r"linkedin", r"linked[-_ ]?in[-_ ]?profile", r"linkedin[-_ ]?url"], linkedin):
            filled_fields.append("linkedin")

        # 9. GitHub Profile
        github = self.profile.get("github", "https://github.com/NITINCHANDER007")
        if github and await self._fill_first_matching([r"github", r"git[-_ ]?url", r"portfolio", r"website"], github):
            filled_fields.append("github")

        # 10. Technical Skills
        skills = self.profile.get("skills", [])
        if skills:
            skills_str = ", ".join(skills)
            if await self._fill_first_matching([r"skills", r"technologies", r"technical[-_ ]?stack"], skills_str, is_textarea=True):
                filled_fields.append("skills")

        # 11. Work Authorization & Sponsorship Questions (Radio / Select / Checkboxes)
        await self._answer_authorization_questions()

        return {
            "filled_count": len(filled_fields),
            "fields": filled_fields
        }

    async def upload_resume(self, resume_path: Optional[str] = None) -> bool:
        """Find and upload resume file."""
        path_to_upload = resume_path or self.profile.get("resume_path")
        if not path_to_upload or not Path(path_to_upload).exists():
            return False

        file_inputs = await self.page.query_selector_all('input[type="file"]')
        for finput in file_inputs:
            try:
                # Check if visible or matches resume/cv in attributes
                name_attr = (await finput.get_attribute("name") or "").lower()
                id_attr = (await finput.get_attribute("id") or "").lower()
                aria_attr = (await finput.get_attribute("aria-label") or "").lower()

                await finput.set_input_files(str(path_to_upload))
                return True
            except Exception:
                continue

        return False

    async def capture_audit_screenshot(self, company: str, job_id: str) -> str:
        """Capture screenshot of the filled application page for user verification."""
        clean_company = re.sub(r"[^\w\-]", "_", company)
        clean_id = re.sub(r"[^\w\-]", "_", str(job_id))
        filename = f"{clean_company}_{clean_id}_review.png"
        filepath = SCREENSHOT_DIR / filename
        try:
            await self.page.screenshot(path=str(filepath), full_page=False)
            return str(filepath)
        except Exception:
            return ""

    async def _fill_first_matching(self, patterns: List[str], value: str, is_textarea: bool = False) -> bool:
        """Locate field by label, placeholder, name, id, or aria-label and fill it."""
        if not value:
            return False

        tag = "textarea" if is_textarea else "input"
        elements = await self.page.query_selector_all(f"{tag}:not([type='hidden']):not([type='submit'])")

        for el in elements:
            try:
                if not await el.is_visible():
                    continue

                name_attr = (await el.get_attribute("name") or "").lower()
                id_attr = (await el.get_attribute("id") or "").lower()
                placeholder = (await el.get_attribute("placeholder") or "").lower()
                aria_label = (await el.get_attribute("aria-label") or "").lower()

                combined = f"{name_attr} {id_attr} {placeholder} {aria_label}"

                # Also inspect parent or sibling label text if available
                label_text = await self.page.evaluate(
                    """el => {
                        const id = el.id;
                        if (id) {
                            const lbl = document.querySelector(`label[for="${id}"]`);
                            if (lbl) return lbl.textContent.toLowerCase();
                        }
                        const parent = el.closest('label') || el.closest('div');
                        return parent ? parent.textContent.toLowerCase() : '';
                    }""",
                    el
                )
                combined = f"{combined} {label_text}"

                for pat in patterns:
                    if re.search(pat, combined, re.IGNORECASE):
                        current_val = await el.input_value()
                        if not current_val.strip():
                            await el.fill(value)
                            await asyncio.sleep(0.05)
                            return True
            except Exception:
                continue

        return False

    async def _answer_authorization_questions(self):
        """Answer common work authorization and sponsorship queries."""
        try:
            # Authorized to work -> Yes
            yes_buttons = await self.page.query_selector_all('input[type="radio"][value*="yes" i], input[type="radio"][value="1"]')
            for r in yes_buttons:
                parent_text = await self.page.evaluate("el => el.closest('div, fieldset')?.textContent || ''", r)
                if re.search(r"legally authorized|eligible to work|authorized to work in", parent_text, re.IGNORECASE):
                    await r.check()
        except Exception:
            pass

