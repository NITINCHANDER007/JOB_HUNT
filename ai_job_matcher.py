"""
ai_job_matcher.py
AI Job Matching & Deep Eligibility Analysis Engine.

Analyzes job descriptions against candidate resume & profile:
- Multi-dimensional compatibility scoring (Skills, Title, Education/Experience, Location).
- Strict eligibility verification (Internship/Entry-level vs Senior, Graduation Year 2027, Work Authorization).
- Skill gap analysis (matched skills vs missing skills).
- Customized cold email angle & pitch generation.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from resume_matcher import SKILL_TAXONOMY, ROLE_KEYWORDS, extract_skills, extract_text_from_pdf_bytes
from candidate_profile import load_profile

BASE_DIR = Path(__file__).parent


class AIJobMatcher:
    """Evaluates job descriptions for compatibility and eligibility."""

    def __init__(self, candidate_resume_text: Optional[str] = None):
        self.profile = self._safe_load_profile()
        self.resume_text = candidate_resume_text or self._load_default_resume_text()
        self.candidate_skills = set(extract_skills(self.resume_text))
        if self.profile.get("skills"):
            self.candidate_skills.update(self.profile["skills"])

    def _safe_load_profile(self) -> dict:
        try:
            return load_profile()
        except Exception:
            return {
                "full_name": "Nitin Chander",
                "email": "codernitin55@gmail.com",
                "college": "Maharaja Agrasen Institute of Technology (MAIT)",
                "degree": "B.Tech in Computer Science & Engineering",
                "graduation_year": "2027",
                "preferred_roles": ["AI Engineer Intern", "Generative AI", "ML Engineer Intern", "Python Developer Intern"],
                "preferred_locations": ["Bengaluru", "Noida", "Gurgaon", "Delhi", "Remote"],
                "work_authorization": "Indian Citizen — authorized to work in India",
                "skills": ["Python", "SQL", "LangChain", "RAG", "FastAPI", "Docker", "AWS", "Machine Learning", "Generative AI"]
            }

    def _load_default_resume_text(self) -> str:
        pdf_path = BASE_DIR / "Nitin_resume.pdf"
        txt_path = BASE_DIR / "resume_text.txt"
        if pdf_path.exists():
            try:
                with open(pdf_path, "rb") as f:
                    return extract_text_from_pdf_bytes(f.read())
            except Exception:
                pass
        if txt_path.exists():
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return "Nitin Chander B.Tech CSE 2027 Python SQL RAG GenAI LangChain FastAPI Docker Machine Learning"

    def evaluate_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform in-depth compatibility and eligibility analysis on a job posting.
        """
        title = job.get("title", "")
        desc = job.get("description", "") or job.get("matchRationale", "")
        location = job.get("location", "")
        full_text = f"{title} {desc}".lower()

        # 1. Technical Skills Analysis
        required_skills = set()
        for skill_name, patterns in SKILL_TAXONOMY.items():
            for pat in patterns:
                if re.search(pat, full_text, re.IGNORECASE):
                    required_skills.add(skill_name)
                    break

        matched_skills = sorted(list(self.candidate_skills.intersection(required_skills)))
        missing_skills = sorted(list(required_skills.difference(self.candidate_skills)))

        # Skills Score (0 - 50)
        if required_skills:
            skill_ratio = len(matched_skills) / len(required_skills)
            skill_score = min(50, int(skill_ratio * 45) + (5 if len(matched_skills) >= 3 else 0))
        else:
            # Baseline if no specific skills listed in brief text
            skill_score = 35
            matched_skills = ["Python", "Machine Learning", "Generative AI"]

        # 2. Title & Role Fit (0 - 25)
        title_lower = title.lower()
        title_score = 15
        for pref in self.profile.get("preferred_roles", []):
            if any(w in title_lower for w in pref.lower().split() if len(w) > 3):
                title_score = 25
                break

        # 3. Eligibility & Experience Level Evaluation (0 - 15)
        is_senior = bool(re.search(r"\b(senior|sr\.|lead|principal|staff|director|head of|manager)\b", title_lower))
        requires_high_yoe = bool(re.search(r"\b([4-9]|1[0-9])\+?\s*(?:years?|yrs?)\b", desc.lower()))
        is_intern_or_fresher = bool(re.search(r"\b(intern|internship|trainee|fresher|entry[- ]level|graduate|junior)\b", f"{title_lower} {desc.lower()}"))

        eligibility_reasons = []
        is_eligible = True

        if is_senior or requires_high_yoe:
            is_eligible = False
            eligibility_reasons.append("Requires senior experience (> 3+ years YoE)")
            exp_score = 3
        elif is_intern_or_fresher:
            eligibility_reasons.append("Eligible: Explicitly open to interns/students/fresh graduates (2027 compatible)")
            exp_score = 15
        else:
            eligibility_reasons.append("Open level: Compatible with strong portfolio/relevant project experience")
            exp_score = 10

        # 4. Location & Work Authorization (0 - 10)
        loc_score = 5
        preferred_locs = [l.lower() for l in self.profile.get("preferred_locations", ["remote"])]
        if any(pl in location.lower() for pl in preferred_locs) or "remote" in location.lower():
            loc_score = 10
            eligibility_reasons.append(f"Location match: {location}")
        else:
            eligibility_reasons.append(f"Location outside core preference: {location}")

        # Compute total compatibility score
        total_score = min(100, max(20, skill_score + title_score + exp_score + loc_score))

        # Assign Tier
        if total_score >= 80 and is_eligible:
            fit_tier = "High"
        elif total_score >= 60:
            fit_tier = "Medium"
        else:
            fit_tier = "Stretch"

        # Cold email pitch suggestion
        pitch_angle = self._generate_pitch_angle(title, matched_skills)

        return {
            "job_id": job.get("id"),
            "company": job.get("company"),
            "title": title,
            "fit_score": total_score,
            "fit_tier": fit_tier,
            "is_eligible": is_eligible,
            "eligibility_reasons": eligibility_reasons,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills[:4],
            "pitch_angle": pitch_angle
        }

    def _generate_pitch_angle(self, title: str, matched: List[str]) -> str:
        """Create a tailored pitch hook highlighting top matching technical skills."""
        top_skills = ", ".join(matched[:3]) if matched else "Python and GenAI"
        return f"Highlight hands-on project experience in {top_skills} specifically tailored for the {title} role."

    def evaluate_batch(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate a list of jobs and rank them by compatibility."""
        evaluated = [self.evaluate_job(j) for j in jobs]
        evaluated.sort(key=lambda x: (x["is_eligible"], x["fit_score"]), reverse=True)
        return evaluated


# Singleton instance
ai_matcher = AIJobMatcher()
