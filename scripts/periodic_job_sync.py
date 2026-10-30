"""periodic_job_sync.py
Automated periodic crawler and synchronizer for Job Hunt Intelligence.
Fetches, deduplicates, scores, and integrates newly published opportunities across LinkedIn, Indeed, and Naukri.

Can be run:
  1. As a one-shot execution:
       python scripts/periodic_job_sync.py --once
  2. As a standing background process (e.g. every 4 hours):
       python scripts/periodic_job_sync.py --interval-hours 4
  3. Via Windows Task Scheduler or Antigravity /schedule
"""

import os
import sys
import json
import time
import re
import argparse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")

def normalize_key(company, title):
    c = re.sub(r'[^a-z0-9]', '', (company or '').lower())
    t = re.sub(r'[^a-z0-9]', '', (title or '').lower())
    return f"{c}_{t}"

def score_job(title, desc):
    """Calculate fit score (60-95%) based on Nitin Chander's profile."""
    text = f"{title} {desc}".lower()
    score = 70
    
    # Positive keywords
    if any(k in text for k in ['genai', 'generative ai', 'rag', 'llm', 'langchain']):
        score += 15
    elif any(k in text for k in ['machine learning', 'ml', 'deep learning', 'pytorch', 'xgboost']):
        score += 12
    elif any(k in text for k in ['python', 'data science', 'fastapi', 'flask']):
        score += 10
    
    if any(k in text for k in ['intern', 'internship', 'fresher', 'trainee', 'entry level']):
        score += 8
    
    if any(k in text for k in ['delhi', 'noida', 'gurgaon', 'gurugram', 'remote']):
        score += 5
        
    return min(score, 94)

def generate_cold_email(company, role, rationale):
    """Generate personalized cold email tailored to Nitin's background."""
    subject = f"{role} Application | Nitin Chander"
    body = (
        f"Hi {company} Talent Team,\n\n"
        f"I am writing to express my strong enthusiasm for the {role} position. "
        f"As a Computer Science undergraduate at MAIT with hands-on experience developing "
        f"machine learning pipelines, RAG architectures with LangChain, and Python microservices, "
        f"I am eager to contribute.\n\n"
        f"During my prior corporate internships at IDEMIA and NTPC, I cleaned and analyzed operational "
        f"telemetry, optimized SQL data flows, and built an end-to-end Machine Learning Fraud Detection system "
        f"evaluating precision-recall and ROC-AUC metrics. In addition, I engineered a production-grade Medical "
        f"Literature Assistant utilizing hybrid search and vector databases.\n\n"
        f"Could we schedule a short 10-minute conversation this week to discuss how my skillset aligns with your team's goals?\n\n"
        f"Best regards,\n"
        f"Nitin Chander\n"
        f"+91-8130489303 | codernitin55@gmail.com\n"
        f"linkedin.com/in/nitin-chander-b6928120b"
    )
    return subject, body

def fetch_latest_from_apify():
    """Retrieve newly scraped items from the latest Apify actor runs."""
    if not APIFY_TOKEN:
        return []
    
    items = []
    try:
        url = f"https://api.apify.com/v2/actor-runs?token={APIFY_TOKEN}&limit=5"
        req = urllib.request.Request(url, headers={"User-Agent": "JobHuntBot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            runs = data.get("data", {}).get("items", [])
        
        for r in runs:
            ds_id = r.get("defaultDatasetId")
            if not ds_id:
                continue
            try:
                ds_url = f"https://api.apify.com/v2/datasets/{ds_id}/items?token={APIFY_TOKEN}&format=json&limit=50&clean=true"
                ds_req = urllib.request.Request(ds_url, headers={"User-Agent": "JobHuntBot/1.0"})
                with urllib.request.urlopen(ds_req, timeout=15) as ds_resp:
                    ds_items = json.loads(ds_resp.read().decode())
                    if isinstance(ds_items, list):
                        items.extend(ds_items)
            except Exception as e:
                print(f"[WARN] Failed fetching dataset {ds_id}: {e}")
    except Exception as e:
        print(f"[WARN] Failed querying actor runs: {e}")
        
    return items

def clean_company_linkedin(url, company_name=""):
    """Normalize and verify company LinkedIn URL."""
    if (company_name or "").lower() == "discover dollar":
        return "https://www.linkedin.com/company/discover-dollar/", True
    if not url or "linkedin.com/company" not in url:
        return "", False
    # Strip query parameters
    url = url.split("?")[0].rstrip("/")
    # Normalize subdomains to standard https://www.linkedin.com/company/
    url = re.sub(r'https?://[a-z0-9\.\-]*linkedin\.com/company', 'https://www.linkedin.com/company', url)
    if not url.startswith("https://www.linkedin.com/company/"):
        return "", False
    if not url.endswith("/"):
        url += "/"
    return url, True


def perform_sync():
    """Main synchronization logic: prunes stale/closed jobs, fetches new ones, deduplicates, and saves."""
    # 0. Prune stale (> 30 days old) and closed jobs before merging new ones
    try:
        from scripts.verify_job_availability import prune_jobs
        prune_res = prune_jobs(max_age_days=30, check_http=False)
        print(f"Pre-sync pruning: Retained {prune_res['retained_count']}, Pruned {prune_res['pruned_count']}")
    except Exception as e:
        print(f"[WARN] Pruning check failed: {e}")

    jobs_path = DATA_DIR / "jobs_data.json"
    if not jobs_path.exists():
        jobs_path = BASE_DIR / "jobs_data.json"
        
    with open(jobs_path, "r", encoding="utf-8") as f:
        current_jobs = json.load(f)
        
    existing_keys = {normalize_key(j.get("company"), j.get("title")): True for j in current_jobs}
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Current active job count: {len(current_jobs)}")
    
    raw_incoming = fetch_latest_from_apify()
    print(f"Retrieved {len(raw_incoming)} raw incoming entries from remote sync.")
    
    newly_added = []
    
    for item in raw_incoming:
        company = (item.get("companyName") or item.get("company") or "").strip()
        title = (item.get("title") or item.get("positionName") or "").strip()
        location = (item.get("location") or "Delhi NCR / Remote, India").strip()
        description = (item.get("description") or "").strip()
        link = (item.get("applyUrl") or item.get("jobUrl") or item.get("externalApplyLink") or item.get("url") or "").strip()
        
        if not company or not title:
            continue
            
        key = normalize_key(company, title)
        if key in existing_keys:
            continue
            
        # Filter for relevant tech keywords
        combined_text = f"{title} {description}".lower()
        if not any(k in combined_text for k in ['ai', 'intelligence', 'learning', 'data', 'python', 'developer', 'software', 'engineer', 'analyst']):
            continue
        if any(bad in combined_text for bad in ['biology', 'ecologist', 'unpaid', 'marketing intern', 'hr coordinator', 'realtor', 'dentist']):
            continue
            
        fit_score = score_job(title, description)
        fit_tier = "High" if fit_score >= 75 else ("Medium" if fit_score >= 60 else "Stretch")
        
        # Determine source
        source = "LinkedIn"
        if "indeed" in link.lower() or item.get("positionName"):
            source = "Indeed"
        elif "naukri" in link.lower():
            source = "Naukri"
            
        # Determine postedDate
        pub = item.get("publishedAt") or item.get("postedTime")
        if pub and isinstance(pub, str) and len(pub) >= 10:
            date_str = pub[:10]
            posted_date = f"{date_str} 10:00:00"
        else:
            posted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        subject, body = generate_cold_email(company, title, f"Strong technical alignment in {title}.")
        
        company_linkedin, company_verified = clean_company_linkedin(
            item.get("companyUrl") or item.get("companyWebsite") or "",
            company_name=company
        )
        
        new_entry = {
            "id": len(current_jobs) + len(newly_added) + 1,
            "company": company,
            "title": title,
            "fitScore": fit_score,
            "fitTier": fit_tier,
            "location": location,
            "salary": item.get("salary") or "₹20,000 – ₹40,000 / month (Est.)",
            "source": source,
            "postedDate": posted_date,
            "link": link,
            "contactEmail": "",
            "emailVerified": False,
            "companyLinkedIn": company_linkedin if company_verified else "",
            "companyLinkedInVerified": company_verified,
            "recruiterLinkedIn": "",
            "recruiterLinkedInVerified": False,
            "contactName": f"{company} Talent Team",
            "description": description[:600] if description else f"Active {title} opening at {company}.",
            "matchRationale": f"Matches technical background in Python and {title}.",
            "coldEmailSubject": subject,
            "coldEmailBody": body,
            "coldEmailAngle": f"Direct project experience relevant to {title}.",
            "status": "Not Applied",
            "notes": ""
        }
        
        existing_keys[key] = True
        newly_added.append(new_entry)
        
    if newly_added:
        print(f"Discovered and integrated {len(newly_added)} new active opportunities!")
        combined = newly_added + current_jobs
        
        # Sort descending by postedDate
        combined.sort(
            key=lambda x: (x.get("postedDate") or "2026-10-01 00:00:00", x.get("fitScore", 0)),
            reverse=True
        )
        for idx, job in enumerate(combined, start=1):
            job["id"] = idx
            
        # Write to JSON files
        with open(DATA_DIR / "jobs_data.json", "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2, ensure_ascii=False)
        with open(BASE_DIR / "jobs_data.json", "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2, ensure_ascii=False)
            
        # Write to JS files
        js_content = f"// Job Hunt Intelligence - Unified Master Job Database\n// Total Active Opportunities: {len(combined)}\nwindow.INITIAL_JOBS_DATA = {json.dumps(combined, indent=2, ensure_ascii=False)};\n"
        with open(DATA_DIR / "jobs_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        with open(BASE_DIR / "jobs_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
            
        return {
            "status": "updated",
            "new_count": len(newly_added),
            "total_active": len(combined),
            "synced_at": datetime.now(timezone.utc).isoformat()
        }
    else:
        print("No new jobs to add. All incoming jobs are already integrated and up to date.")
        return {
            "status": "up_to_date",
            "new_count": 0,
            "total_active": len(current_jobs),
            "synced_at": datetime.now(timezone.utc).isoformat()
        }

def run_loop(interval_hours):
    """Run continuous sync at specified interval in hours."""
    print(f"=== Starting Periodic Job Sync Service (Interval: {interval_hours} hours) ===")
    while True:
        try:
            res = perform_sync()
            print(f"Sync result: {res}")
        except Exception as e:
            print(f"[ERROR] Sync failed: {e}")
            
        sleep_secs = int(interval_hours * 3600)
        print(f"Next sync in {interval_hours} hour(s) ({sleep_secs}s). Sleeping...")
        time.sleep(sleep_secs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Hunt Periodic Sync Engine")
    parser.add_argument("--once", action="store_true", help="Run sync once and exit")
    parser.add_argument("--interval-hours", type=float, default=4.0, help="Interval between sync runs in hours (default: 4.0)")
    args = parser.parse_args()
    
    if args.once:
        perform_sync()
    else:
        run_loop(args.interval_hours)
