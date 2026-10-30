"""
resume_matcher.py
Extracts text from PDF/DOCX/TXT resumes, extracts key skills,
and computes fit scores against job opportunities.
"""

import os
import re
import io
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Core skill taxonomy for matching
SKILL_TAXONOMY = {
    # AI & GenAI
    "Generative AI": [r"\bgenerative ai\b", r"\bgenai\b", r"\bgen ai\b"],
    "LLMs": [r"\bllm\b", r"\bllms\b", r"\blarge language model\b"],
    "RAG": [r"\brag\b", r"\bretrieval[- ]augmented\b"],
    "LangChain": [r"\blangchain\b"],
    "LangGraph": [r"\blanggraph\b"],
    "Prompt Engineering": [r"\bprompt engineering\b"],
    "Transformers": [r"\btransformers?\b", r"\bhugging face\b", r"\bhuggingface\b"],
    "NLP": [r"\bnlp\b", r"\bnatural language processing\b"],
    "ChromaDB": [r"\bchromadb\b", r"\bchroma\b"],
    "FAISS": [r"\bfaiss\b"],
    "Vector Search": [r"\bvector (?:database|db|search|embeddings?)\b"],
    "Computer Vision": [r"\bcomputer vision\b", r"\bcv\b", r"\bopencv\b"],

    # Machine Learning & Data Science
    "Python": [r"\bpython\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Deep Learning": [r"\bdeep learning\b", r"\bdl\b"],
    "Scikit-learn": [r"\bscikit[- ]learn\b", r"\bsklearn\b"],
    "PyTorch": [r"\bpytorch\b"],
    "TensorFlow": [r"\btensorflow\b", r"\bkeras\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "XGBoost": [r"\bxgboost\b"],
    "Data Science": [r"\bdata science\b", r"\bdata scientist\b"],
    "Feature Engineering": [r"\bfeature engineering\b"],
    "Statistics": [r"\bstatistics\b", r"\bstatistical\b"],

    # Data Engineering & Pipelines
    "SQL": [r"\bsql\b", r"\bpostgresql\b", r"\bmysql\b", r"\bsqlite\b"],
    "Data Engineering": [r"\bdata engineering\b", r"\bdata engineer\b", r"\betl\b"],
    "Data Pipelines": [r"\bdata pipelines?\b"],
    "PySpark": [r"\bpyspark\b", r"\bspark\b", r"\bapache spark\b"],
    "Databricks": [r"\bdatabricks\b"],
    "Airflow": [r"\bairflow\b", r"\bapache airflow\b"],
    "dbt": [r"\bdbt\b"],
    "Kafka": [r"\bkafka\b"],
    "Data Modeling": [r"\bdata model(?:ling|s)?\b", r"\bstar schema\b"],
    "BigQuery": [r"\bbigquery\b"],
    "Snowflake": [r"\bsnowflake\b"],

    # Backend & DevOps
    "FastAPI": [r"\bfastapi\b"],
    "Flask": [r"\bflask\b"],
    "REST APIs": [r"\brest\b", r"\brestful\b", r"\bapis?\b"],
    "Docker": [r"\bdocker\b", r"\bcontainer(?:s|ization)?\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b", r"\bec2\b", r"\bs3\b"],
    "Azure": [r"\bazure\b"],
    "GCP": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Git": [r"\bgit\b", r"\bgithub\b"],
    "CI/CD": [r"\bci/cd\b", r"\bgithub actions\b"],
    "MLflow": [r"\bmlflow\b", r"\bmlops\b"],
    "System Design": [r"\bsystem design\b"],
    "DSA": [r"\bdsa\b", r"\bdata structures\b", r"\balgorithms\b"],
}

ROLE_KEYWORDS = {
    "AI Engineer": ["ai engineer", "artificial intelligence", "genai", "generative ai", "agentic", "llm"],
    "Machine Learning": ["machine learning", "ml engineer", "deep learning"],
    "Data Scientist": ["data scientist", "data science"],
    "Data Engineer": ["data engineer", "data platform", "etl", "databricks", "spark", "pipeline"],
    "Data Analyst": ["data analyst", "analytics", "business intelligence", "bi"],
    "Backend Developer": ["backend", "python developer", "software engineer", "fastapi", "flask"],
    "Intern": ["intern", "internship", "trainee", "entry level", "fresher", "junior"]
}


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF byte content."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages_text = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages_text).strip()
    except Exception as e:
        # Fallback to PyMuPDF if available
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = "\n".join([page.get_text() for page in doc])
            return text.strip()
        except Exception:
            raise RuntimeError(f"Could not parse PDF: {e}")


def extract_text_from_docx_bytes(docx_bytes: bytes) -> str:
    """Extract plain text from DOCX byte stream without external docx dependency."""
    import zipfile
    import xml.etree.ElementTree as ET
    try:
        with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            # Find all text tags <w:t>
            texts = []
            for elem in tree.iter():
                if elem.tag.endswith("}t"):
                    if elem.text:
                        texts.append(elem.text)
            return " ".join(texts)
    except Exception as e:
        raise RuntimeError(f"Could not parse DOCX: {e}")


def extract_skills(text: str) -> List[str]:
    """Find all matching taxonomy skills in the resume text."""
    lower_text = text.lower()
    found = []
    for skill, patterns in SKILL_TAXONOMY.items():
        for pat in patterns:
            if re.search(pat, lower_text, re.IGNORECASE):
                found.append(skill)
                break
    return sorted(found)


def extract_profile_info(text: str) -> Dict[str, Any]:
    """Extract basic candidate metadata (name, email, phone, skills)."""
    # Email
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    email = email_match.group(0) if email_match else ""

    # Phone
    phone_match = re.search(r"(?:\+91[\-\s]?)?[6789]\d{9}|\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b", text)
    phone = phone_match.group(0) if phone_match else ""

    # Name: First non-empty line or capitalized line
    name = ""
    for line in text.splitlines():
        clean = line.strip()
        if clean and not any(sym in clean for sym in ["@", "http", "+", "|", "Resume"]):
            if len(clean.split()) <= 4 and re.match(r"^[A-Za-z\s.]+$", clean):
                name = clean
                break

    skills = extract_skills(text)

    # Detect role inclination from resume text
    lower = text.lower()
    preferred_roles = []
    for role, kws in ROLE_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            preferred_roles.append(role)

    return {
        "name": name or "Candidate",
        "email": email,
        "phone": phone,
        "skills": skills,
        "skills_count": len(skills),
        "preferred_roles": preferred_roles,
        "word_count": len(text.split())
    }


def score_job_against_resume(job: Dict[str, Any], resume_skills: List[str], resume_text: str) -> Dict[str, Any]:
    """
    Computes an exact fit score (0-100) and matched skills list for a given job.
    """
    job_title = (job.get("title") or "").lower()
    job_desc = (job.get("description") or "").lower()
    job_rationale = (job.get("matchRationale") or "").lower()
    combined_job_text = f"{job_title} {job_desc} {job_rationale}"

    resume_skills_set = set(resume_skills)

    # 1. Title / Domain matching (up to 40 pts)
    title_score = 0
    if any(k in job_title for k in ["ai", "genai", "generative ai", "llm", "agentic", "agent"]):
        if any(s in resume_skills_set for s in ["Generative AI", "LLMs", "RAG", "LangChain", "Prompt Engineering"]):
            title_score = 40
        else:
            title_score = 25
    elif any(k in job_title for k in ["machine learning", "ml", "deep learning"]):
        if any(s in resume_skills_set for s in ["Machine Learning", "Scikit-learn", "PyTorch", "TensorFlow"]):
            title_score = 40
        else:
            title_score = 25
    elif any(k in job_title for k in ["data scientist", "data science"]):
        if any(s in resume_skills_set for s in ["Data Science", "Python", "SQL", "Pandas", "Scikit-learn"]):
            title_score = 38
        else:
            title_score = 24
    elif any(k in job_title for k in ["data engineer", "data platform", "etl", "spark", "databricks"]):
        if any(s in resume_skills_set for s in ["SQL", "Python", "Data Engineering", "PySpark", "Databricks", "Airflow"]):
            title_score = 38
        else:
            title_score = 22
    elif any(k in job_title for k in ["python", "backend", "software engineer", "developer"]):
        if any(s in resume_skills_set for s in ["Python", "FastAPI", "Flask", "REST APIs", "SQL"]):
            title_score = 36
        else:
            title_score = 20
    else:
        title_score = 15

    # 2. Skills overlap (up to 40 pts)
    matched_skills = []
    for skill in resume_skills:
        patterns = SKILL_TAXONOMY.get(skill, [])
        for pat in patterns:
            if re.search(pat, combined_job_text, re.IGNORECASE):
                matched_skills.append(skill)
                break

    # Also detect skills from job title directly if matched
    for s in ["Python", "Machine Learning", "NLP", "Prompt Engineering", "SQL", "Pandas", "Scikit-learn", "FastAPI"]:
        if s in resume_skills_set and s.lower() in job_title and s not in matched_skills:
            matched_skills.append(s)

    skill_overlap_ratio = min(1.0, len(matched_skills) / 4.0) if matched_skills else 0.1
    skill_score = int(skill_overlap_ratio * 40)

    # 3. Experience level alignment (up to 12 pts)
    exp_score = 0
    if any(k in job_title or k in combined_job_text for k in ["intern", "internship", "trainee", "fresher", "entry level", "graduate", "junior", "associate"]):
        exp_score = 12
    else:
        exp_score = 8

    # 4. Location match (up to 8 pts)
    loc_score = 8  # Default positive for Bangalore/Noida/Remote
    loc = (job.get("location") or "").lower()
    if any(city in loc for city in ["noida", "delhi", "gurgaon", "bengaluru", "bangalore", "remote", "hybrid"]):
        loc_score = 8
    else:
        loc_score = 4

    total_score = title_score + skill_score + exp_score + loc_score
    # Cap between 45 and 98
    total_score = max(48, min(98, total_score))

    tier = "High" if total_score >= 75 else ("Medium" if total_score >= 60 else "Stretch")

    return {
        "matchScore": total_score,
        "matchedSkills": matched_skills[:6],
        "matchTier": tier
    }


def score_all_jobs(jobs: List[Dict[str, Any]], resume_text: str) -> Dict[str, Any]:
    """Scores all jobs against resume text and returns sorted list."""
    profile_info = extract_profile_info(resume_text)
    resume_skills = profile_info["skills"]

    scored_jobs = []
    for j in jobs:
        copy_j = dict(j)
        score_data = score_job_against_resume(j, resume_skills, resume_text)
        copy_j["fitScore"] = score_data["matchScore"]
        copy_j["fitTier"] = score_data["matchTier"]
        copy_j["matchedSkills"] = score_data["matchedSkills"]
        copy_j["resumeMatchScore"] = score_data["matchScore"]
        scored_jobs.append(copy_j)

    # Sort descending by resume match score (highest fit first!)
    scored_jobs.sort(key=lambda x: (x.get("resumeMatchScore", 0), x.get("postedDate", "")), reverse=True)

    return {
        "profile": profile_info,
        "jobs": scored_jobs,
        "total_jobs": len(scored_jobs),
        "high_matches": sum(1 for j in scored_jobs if j.get("fitTier") == "High")
    }

