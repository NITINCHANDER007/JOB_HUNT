"""
apply_engine/smart_form_filler.py
Intelligent Form Filling Engine using Playwright.

Analyzes web application pages, identifies field semantics via labels,
placeholders, and ARIA attributes, auto-fills candidate details
with resume and cover letter upload support, and screening question answering.

ETHICAL RULES:
- Never fabricate answers to unknown questions.
- If required information is missing, records the question and prompts user.
"""

import os
import re
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.async_api import Page, ElementHandle

BASE_DIR = Path(__file__).parent.parent
SCREENSHOT_DIR = BASE_DIR / "exports" / "apply_screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
QA_KB_FILE = Path(__file__).parent / "qa_knowledge_base.json"


class SmartFormFiller:
    """Intelligently detects and populates job application forms."""

    def __init__(self, page: Page, profile: Dict[str, Any]):
        self.page = page
        self.profile = profile
        self.kb = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load screening Q&A knowledge base."""
        if QA_KB_FILE.exists():
            try:
                with open(QA_KB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    async def auto_fill(self, company: str = "", role: str = "") -> Dict[str, Any]:
        """Inspect and fill all detectable fields on the page."""
        filled_fields = []

        # 1. Full name or First / Last Name
        full_name = self.profile.get("full_name", "Nitin Chander")
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

        # 2. Email Address (strictly uses candidate profile email, e.g. codernitin55@gmail.com)
        if await self._fill_first_matching([r"email", r"e[-_ ]?mail"], self.profile.get("email", "codernitin55@gmail.com")):
            filled_fields.append("email")

        # 3. Phone Number
        if await self._fill_first_matching([r"phone", r"mobile", r"contact[-_ ]?number", r"tel"], self.profile.get("phone", "+91-8130489303")):
            filled_fields.append("phone")

        # 4. College / University
        college = self.profile.get("college", "Maharaja Agrasen Institute of Technology (MAIT)")
        if await self._fill_first_matching([r"college", r"university", r"school", r"institution"], college):
            filled_fields.append("college")

        # 5. Degree / Major
        degree = self.profile.get("degree", "B.Tech in Computer Science & Engineering")
        if await self._fill_first_matching([r"degree", r"major", r"field[-_ ]?of[-_ ]?study", r"course"], degree):
            filled_fields.append("degree")

        # 6. Graduation Year
        grad_year = str(self.profile.get("graduation_year", "2027"))
        if await self._fill_first_matching([r"graduat(?:ion|ed)[-_ ]?year", r"passing[-_ ]?year", r"batch"], grad_year):
            filled_fields.append("graduation_year")

        # 7. CGPA / Marks
        cgpa = str(self.profile.get("cgpa", "8.0"))
        if await self._fill_first_matching([r"cgpa", r"gpa", r"percentage", r"grade"], cgpa):
            filled_fields.append("cgpa")

        # 8. LinkedIn Profile
        linkedin = self.profile.get("linkedin", "https://linkedin.com/in/nitin-chander-b6928120b")
        if linkedin and await self._fill_first_matching([r"linkedin", r"linked[-_ ]?in[-_ ]?profile", r"linkedin[-_ ]?url"], linkedin):
            filled_fields.append("linkedin")

        # 9. GitHub Profile / Website
        github = self.profile.get("github", "https://github.com/NITINCHANDER007")
        if github and await self._fill_first_matching([r"github", r"git[-_ ]?url", r"portfolio", r"website"], github):
            filled_fields.append("github")

        # 10. Technical Skills
        skills = self.profile.get("skills", [])
        if skills:
            skills_str = ", ".join(skills)
            if await self._fill_first_matching([r"skills", r"technologies", r"technical[-_ ]?stack"], skills_str, is_textarea=True):
                filled_fields.append("skills")

        # 11. Role applying for (if field present)
        target_role = role or "AI Engineer Intern"
        if await self._fill_first_matching([r"role[-_ ]?interest", r"position[-_ ]?applied", r"job[-_ ]?title"], target_role):
            filled_fields.append("role_interest")

        # 12. Cover Letter / Note
        cover_note = self.generate_cover_note(company=company, role=role)
        if await self._fill_first_matching([r"cover[-_ ]?note", r"cover[-_ ]?letter", r"why[-_ ]?join", r"message[-_ ]?to[-_ ]?hiring"], cover_note, is_textarea=True):
            filled_fields.append("cover_letter")

        # 13. Answer Screening Questions via Knowledge Base
        kb_filled = await self._answer_screening_questions()
        filled_fields.extend(kb_filled)

        # 14. Check for any required fields that remain unanswered
        unanswered = await self.detect_unanswered_required_fields()

        return {
            "filled_count": len(filled_fields),
            "fields": filled_fields,
            "unanswered_required": unanswered
        }

    def generate_cover_note(self, company: str = "", role: str = "") -> str:
        """Generate a tailored cover note using verified candidate details."""
        comp_str = company or "the team"
        role_str = role or "the engineering opening"
        candidate_name = self.profile.get("full_name", "Nitin Chander")
        phone = self.profile.get("phone", "+91-8130489303")
        email = self.profile.get("email", "codernitin55@gmail.com")

        return (
            f"Dear {comp_str} Hiring Team,\n\n"
            f"I am writing to express my strong enthusiasm for {role_str}. "
            "As a Computer Science & Engineering undergraduate at MAIT with practical experience "
            "building production-grade Python pipelines, LangChain RAG architectures, and REST microservices, "
            f"I am eager to contribute directly to {comp_str}'s technical milestones.\n\n"
            "During my previous corporate engineering internships at IDEMIA and NTPC, I optimized database query workflows "
            "and engineered end-to-end Machine Learning systems. I value writing maintainable, clean code and collaborating "
            "effectively in high-tempo environments.\n\n"
            "Thank you for considering my application. I look forward to the opportunity to speak with your team.\n\n"
            f"Best regards,\n{candidate_name}\n{phone} | {email}"
        )

    async def upload_resume(self, resume_path: Optional[str] = None) -> bool:
        """Find and upload candidate resume file."""
        path_to_upload = resume_path or self.profile.get("resume_path")
        if not path_to_upload or not Path(path_to_upload).exists():
            return False

        file_inputs = await self.page.query_selector_all('input[type="file"]')
        for finput in file_inputs:
            try:
                name_attr = (await finput.get_attribute("name") or "").lower()
                id_attr = (await finput.get_attribute("id") or "").lower()
                aria_attr = (await finput.get_attribute("aria-label") or "").lower()

                # If multiple file inputs, ensure this one is for resume / cv
                if "cover" in name_attr or "cover" in id_attr or "cover" in aria_attr:
                    continue

                await finput.set_input_files(str(path_to_upload))
                return True
            except Exception:
                continue

        return False

    async def upload_cover_letter(self, cover_letter_path: Optional[str] = None) -> bool:
        """Find and upload cover letter file if a separate file input exists."""
        if not cover_letter_path or not Path(cover_letter_path).exists():
            return False

        file_inputs = await self.page.query_selector_all('input[type="file"]')
        for finput in file_inputs:
            try:
                name_attr = (await finput.get_attribute("name") or "").lower()
                id_attr = (await finput.get_attribute("id") or "").lower()
                aria_attr = (await finput.get_attribute("aria-label") or "").lower()

                if "cover" in name_attr or "cover" in id_attr or "cover" in aria_attr:
                    await finput.set_input_files(str(cover_letter_path))
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

    async def detect_unanswered_required_fields(self) -> List[Dict[str, str]]:
        """
        Identify any required form fields that remain empty.
        Strict Safety Rule: Never guess or invent answers!
        """
        unanswered = []
        try:
            # Query inputs, selects, and textareas marked as required
            candidates = await self.page.query_selector_all(
                "input:not([type='hidden']):not([type='submit']), textarea, select"
            )

            for el in candidates:
                if not await el.is_visible():
                    continue

                is_req = await el.get_attribute("required") is not None
                is_aria_req = await el.get_attribute("aria-required") == "true"
                tag_name = await self.page.evaluate("el => el.tagName.toLowerCase()", el)
                input_type = (await el.get_attribute("type") or "text").lower()

                # Get label / context text
                label_text = await self.page.evaluate(
                    """el => {
                        const id = el.id;
                        if (id) {
                            const lbl = document.querySelector(`label[for="${id}"]`);
                            if (lbl) return lbl.textContent.trim();
                        }
                        const parent = el.closest('label') || el.closest('.field') || el.closest('div');
                        return parent ? parent.textContent.slice(0, 150).trim() : '';
                    }""",
                    el
                )

                if "*" in label_text or is_req or is_aria_req:
                    # Check if empty
                    if tag_name == "select":
                        val = await el.input_value()
                        if not val or val == "0" or "select" in val.lower():
                            unanswered.append({"question": label_text, "type": "select", "id": await el.get_attribute("id") or ""})
                    elif input_type in ["radio", "checkbox"]:
                        # Check if at least one in the group is checked
                        name = await el.get_attribute("name")
                        if name:
                            checked = await self.page.query_selector(f"input[name='{name}']:checked")
                            if not checked and not any(u["id"] == name for u in unanswered):
                                unanswered.append({"question": label_text, "type": input_type, "id": name})
                    else:
                        val = await el.input_value()
                        if not val or not val.strip():
                            unanswered.append({"question": label_text, "type": input_type, "id": await el.get_attribute("id") or ""})

        except Exception as e:
            print(f"[smart_form_filler] Error checking unanswered fields: {e}")

        return unanswered

    async def save_custom_answer(self, question_key: str, question_patterns: List[str], answer: str, qtype: str = "text"):
        """Save a newly answered question into the Knowledge Base for future auto-applications."""
        self.kb[question_key] = {
            "question_patterns": question_patterns,
            "answer": answer,
            "type": qtype
        }
        try:
            with open(QA_KB_FILE, "w", encoding="utf-8") as f:
                json.dump(self.kb, f, indent=2)
            print(f"[smart_form_filler] Saved answer for '{question_key}' to knowledge base.")
        except Exception as e:
            print(f"[smart_form_filler] Failed to persist answer to KB: {e}")

    # ── Internal Helpers ─────────────────────────────────────────────────── #

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

    async def _answer_screening_questions(self) -> List[str]:
        """Answer common screening questions (inputs, selects, radios) via Knowledge Base."""
        answered = []
        for key, entry in self.kb.items():
            patterns = entry.get("question_patterns", [])
            answer_val = entry.get("answer", "")
            qtype = entry.get("type", "text")

            # 1. Radio buttons (e.g. Yes/No)
            if qtype == "boolean":
                radios = await self.page.query_selector_all('input[type="radio"]')
                for r in radios:
                    try:
                        parent_text = await self.page.evaluate("el => el.closest('div, fieldset, tr')?.textContent || ''", r)
                        if any(re.search(p, parent_text, re.IGNORECASE) for p in patterns):
                            val = (await r.get_attribute("value") or "").lower()
                            aria_label = (await r.get_attribute("aria-label") or "").lower()
                            r_text = await self.page.evaluate("el => el.parentElement?.textContent || ''", r)
                            combined_r = f"{val} {aria_label} {r_text}".lower()

                            target_state = answer_val.lower() == "yes"
                            is_yes_radio = "yes" in combined_r or val == "1" or val == "true"
                            is_no_radio = "no" in combined_r or val == "0" or val == "false"

                            if (target_state and is_yes_radio) or (not target_state and is_no_radio):
                                await r.check()
                                answered.append(key)
                                break
                    except Exception:
                        continue

            # 2. Dropdown / Select elements
            selects = await self.page.query_selector_all("select")
            for sel in selects:
                try:
                    parent_text = await self.page.evaluate("el => el.closest('div, .field, tr')?.textContent || ''", sel)
                    if any(re.search(p, parent_text, re.IGNORECASE) for p in patterns):
                        # Match option
                        options = await sel.query_selector_all("option")
                        for opt in options:
                            opt_text = (await opt.inner_text()).strip()
                            opt_val = await opt.get_attribute("value") or ""
                            if answer_val.lower() in opt_text.lower() or answer_val.lower() == opt_val.lower():
                                await sel.select_option(value=opt_val)
                                answered.append(key)
                                break
                except Exception:
                    continue

            # 3. Numeric or short text inputs
            if qtype in ["numeric", "text"]:
                if await self._fill_first_matching(patterns, str(answer_val)):
                    answered.append(key)

        return answered
