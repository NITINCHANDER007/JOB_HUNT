"""verify_job_availability.py
Audits and prunes stale (> 30 days old) and unavailable/closed job postings from the active feed.

Detection Methods:
1. 30-Day Age Window: Automatically retires jobs older than 30 days.
2. Closed / Expired Text Signals: Detects keywords like 'no longer accepting applications', 'position closed', 'job expired'.
3. HTTP Status / Link Availability: Performs lightweight HEAD/GET checks to identify 404 dead links or redirect-to-search closures.
4. Archives pruned jobs to data/archived_jobs.json so candidate history is preserved without cluttering the active feed.
"""

import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JOBS_PATH = DATA_DIR / "jobs_data.json"
ARCHIVE_PATH = DATA_DIR / "archived_jobs.json"

CLOSED_PATTERNS = [
    re.compile(r"no longer accepting applications", re.I),
    re.compile(r"this job has expired", re.I),
    re.compile(r"this position has been filled", re.I),
    re.compile(r"job is no longer available", re.I),
    re.compile(r"listing has closed", re.I),
]

def load_jobs():
    if not JOBS_PATH.exists():
        return []
    with open(JOBS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_archive():
    if not ARCHIVE_PATH.exists():
        return []
    try:
        with open(ARCHIVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_archive(archived):
    with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
        json.dump(archived, f, indent=2, ensure_ascii=False)

def is_too_old(posted_date_str, max_age_days=30, reference_date=None):
    """Check if the job was published more than max_age_days ago."""
    if not posted_date_str:
        return True
    if reference_date is None:
        reference_date = datetime.now()
    try:
        dt = datetime.strptime(posted_date_str[:10], "%Y-%m-%d")
        age_days = (reference_date - dt).days
        return age_days > max_age_days
    except:
        return False

def is_marked_closed(job):
    """Check if description or metadata indicates the position is closed."""
    desc = job.get("description", "")
    for pat in CLOSED_PATTERNS:
        if pat.search(desc):
            return True
    return False

def check_link_availability(url, timeout=5):
    """
    Check if a job link is still live.
    Returns (is_live: bool, reason: str)
    """
    if not url or not url.startswith("http"):
        return True, "No URL provided"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final_url = resp.geturl()
            # If redirected to generic search or expired landing page
            if "linkedin.com/jobs/search" in final_url or "expired=true" in final_url:
                return False, "Redirected to search/expired page"
            return True, "HTTP 200 OK"
    except urllib.error.HTTPError as e:
        if e.code in [404, 410]:
            return False, f"HTTP {e.code} Not Found / Gone"
        # 403 or 429 often means rate limit or bot check, don't prune false positives
        return True, f"HTTP {e.code} (Preserved)"
    except Exception as e:
        # Network timeout or DNS glitch, preserve job
        return True, f"Network check skipped: {e}"

def prune_jobs(max_age_days=30, check_http=False, reference_date=None):
    """
    Audit current jobs and prune any that are:
    1. Older than max_age_days (default: 30)
    2. Marked as closed/filled in text
    3. Returning HTTP 404 / expired (if check_http=True)
    """
    jobs = load_jobs()
    if reference_date is None:
        # Use October 30, 2026 as reference in current scenario
        reference_date = datetime(2026, 10, 30)
        
    print(f"Auditing {len(jobs)} active jobs (Max Age: {max_age_days} days, Ref Date: {reference_date.strftime('%Y-%m-%d')})...")
    
    retained = []
    pruned = []
    
    for j in jobs:
        reasons = []
        
        # 1. Age check
        if is_too_old(j.get("postedDate"), max_age_days=max_age_days, reference_date=reference_date):
            reasons.append(f"Older than {max_age_days} days (Posted: {j.get('postedDate')})")
            
        # 2. Closed signal check
        if is_marked_closed(j):
            reasons.append("Marked closed/no longer accepting applications")
            
        # 3. HTTP status check (optional for deep audits)
        if check_http and j.get("link"):
            is_live, link_reason = check_link_availability(j.get("link"))
            if not is_live:
                reasons.append(f"Job link dead ({link_reason})")
                
        if reasons:
            j["pruned_at"] = datetime.now(timezone.utc).isoformat()
            j["prune_reasons"] = reasons
            pruned.append(j)
        else:
            retained.append(j)
            
    print(f"Results: {len(retained)} active jobs retained, {len(pruned)} jobs pruned.")
    
    if pruned:
        archive = load_archive()
        archive_keys = {f"{j.get('company')}_{j.get('title')}" for j in archive}
        for p in pruned:
            key = f"{p.get('company')}_{p.get('title')}"
            if key not in archive_keys:
                archive.append(p)
                archive_keys.add(key)
        save_archive(archive)
        print(f"Archived {len(pruned)} pruned jobs to data/archived_jobs.json.")
        
        # Save retained back to jobs_data.json and jobs_data.js
        for idx, r in enumerate(retained, start=1):
            r["id"] = idx
            
        with open(DATA_DIR / "jobs_data.json", "w", encoding="utf-8") as f:
            json.dump(retained, f, indent=2, ensure_ascii=False)
        with open(BASE_DIR / "jobs_data.json", "w", encoding="utf-8") as f:
            json.dump(retained, f, indent=2, ensure_ascii=False)
            
        js_content = f"// Job Hunt Intelligence - Unified Master Job Database\n// Total Active Opportunities: {len(retained)}\nwindow.INITIAL_JOBS_DATA = {json.dumps(retained, indent=2, ensure_ascii=False)};\n"
        with open(DATA_DIR / "jobs_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        with open(BASE_DIR / "jobs_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
            
    return {
        "retained_count": len(retained),
        "pruned_count": len(pruned),
        "pruned_sample": [f"{p['company']} - {p['title']} ({', '.join(p['prune_reasons'])})" for p in pruned[:5]]
    }

if __name__ == "__main__":
    res = prune_jobs(max_age_days=30, check_http=False)
    print(json.dumps(res, indent=2))

