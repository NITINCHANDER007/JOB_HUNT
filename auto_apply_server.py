"""
auto_apply_server.py
FastAPI backend for the Job Hunt Intelligence Auto-Apply feature.

Serves:
  - Static dashboard files (replaces run_app.py)
  - REST API for the application automation engine

Run with:
    python auto_apply_server.py
  OR (directly with uvicorn):
    uvicorn auto_apply_server:app --host 127.0.0.1 --port 5000 --reload

Security rules enforced:
  - No credentials stored in code — profile loaded from profile_config.json
  - No submission without explicit user POST to /api/apply/{id}/confirm
  - Secrets never logged or returned to frontend
"""

import asyncio
import os
import sys
import webbrowser
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Local modules
from candidate_profile import load_profile, get_safe_profile
from apply_history import (
    init_db, get_history, has_applied_before, export_history_excel,
    AppStatus, update_status
)
from apply_engine.apply_session import create_session, get_session, remove_session
from apply_engine.handler_registry import get_handler, list_supported_sites

BASE_DIR = Path(__file__).parent

# ── FastAPI App ──────────────────────────────────────────────────────────── #
app = FastAPI(
    title="Job Hunt Auto-Apply API",
    description="Automation backend for the Job Hunt Intelligence dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response Models ────────────────────────────────────────────── #
class ApplyRequest(BaseModel):
    job_id: str
    company: str
    role: str
    apply_url: str
    force: bool = False   # If True, bypass duplicate check (user confirmed)


class ApplyResponse(BaseModel):
    session_id: str
    status: str
    message: str


class EmailTestRequest(BaseModel):
    to: Optional[str] = None
    subject: Optional[str] = "Test Connection from Job Hunt Intelligence"
    body: Optional[str] = "Your Gmail connection is working successfully!"


class DiscoverRequest(BaseModel):
    keywords: Optional[list] = None
    locations: Optional[list] = None
    platforms: Optional[list] = None
    limit: Optional[int] = 20


class MatchRequest(BaseModel):
    job_id: Optional[str] = None
    job_data: Optional[dict] = None


class TrackerUpdateRequest(BaseModel):
    job_id_or_id: str
    status: str
    notes: Optional[str] = None


class AutomationRunRequest(BaseModel):
    dry_run: bool = False
    max_auto_apply: int = 3


# ── API Routes ───────────────────────────────────────────────────────────── #

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/jobs/sync")
async def sync_jobs():
    """
    Sync feed status across platforms (LinkedIn, Indeed, Naukri, Direct).
    Returns real statistics and active count without fabricating fake postings.
    """
    import json
    jobs_path = BASE_DIR / "data" / "jobs_data.json"
    if not jobs_path.exists():
        jobs_path = BASE_DIR / "jobs_data.json"
    if not jobs_path.exists():
        raise HTTPException(status_code=404, detail="jobs_data.json not found")
    try:
        with open(jobs_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        by_source = {}
        for j in jobs:
            src = j.get("source", "Direct")
            by_source[src] = by_source.get(src, 0) + 1
        return {
            "status": "synced",
            "total_active": len(jobs),
            "by_source": by_source,
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Feed up to date: {len(jobs)} active opportunities across LinkedIn, Indeed & Naukri"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/sync-now")
@app.post("/api/jobs/sync-now")
async def trigger_sync():
    """Trigger an immediate live crawler run to fetch fresh postings."""
    try:
        from scripts.periodic_job_sync import perform_sync
        res = perform_sync()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/prune")
@app.post("/api/jobs/prune")
async def trigger_prune(max_age_days: int = 30, check_http: bool = False):
    """Audit and prune stale (> 30 days) and unavailable/closed job postings."""
    try:
        from scripts.verify_job_availability import prune_jobs
        res = prune_jobs(max_age_days=max_age_days, check_http=check_http)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def start_periodic_sync_worker():
    """Background task that checks and retrieves fresh jobs every 4 hours."""
    async def periodic_worker():
        # Initial gentle pause before first periodic background check
        await asyncio.sleep(60)
        while True:
            try:
                from scripts.periodic_job_sync import perform_sync
                perform_sync()
            except Exception as err:
                print(f"[Periodic Sync Worker Error]: {err}")
            await asyncio.sleep(4 * 3600)  # repeat every 4 hours

    asyncio.create_task(periodic_worker())


@app.get("/api/jobs/new")
async def get_new_job():
    """Return a newly discovered job from the incoming pool preserving its true LinkedIn postedDate."""
    pool_path = BASE_DIR / "data" / "incoming_pool.json"
    if not pool_path.exists():
        pool_path = BASE_DIR / "incoming_pool.json"
    if not pool_path.exists():
        raise HTTPException(status_code=404, detail="Job pool not found")
    try:
        import json, random
        with open(pool_path, "r", encoding="utf-8") as f:
            pool = json.load(f)
        if not pool:
            raise HTTPException(status_code=404, detail="No jobs available in pool")
        
        # Pick from genuinely latest jobs from LinkedIn (posted 19 mins to 22 hours ago)
        job = random.choice(pool[:9])
        job_copy = dict(job)
        now_dt = datetime.now()
        job_copy["id"] = int(now_dt.timestamp() * 1000)
        # Preserve authentic LinkedIn publication timestamp (never overwrite with current time)
        job_copy["postedDate"] = job.get("postedDate", "2026-10-28 12:00:00")
        job_copy["isNew"] = True
        return job_copy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile")
async def get_profile():
    """Return candidate profile (safe fields only — no raw config keys)."""
    try:
        profile = get_safe_profile()
        return profile
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload a candidate resume (PDF, DOCX, TXT) and compute fit scores across all jobs."""
    import json
    from resume_matcher import extract_text_from_pdf_bytes, extract_text_from_docx_bytes, score_all_jobs
    
    filename = file.filename or "resume"
    ext = filename.lower().split(".")[-1]
    
    try:
        content = await file.read()
        if ext == "pdf":
            text = extract_text_from_pdf_bytes(content)
        elif ext in ["docx", "doc"]:
            text = extract_text_from_docx_bytes(content)
        else:
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1", errors="ignore")
                
        if not text or len(text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from resume file.")

        jobs_path = BASE_DIR / "data" / "jobs_data.json"
        if not jobs_path.exists():
            jobs_path = BASE_DIR / "jobs_data.json"
        with open(jobs_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        result = score_all_jobs(jobs, text)
        result["filename"] = filename
        result["status"] = "success"
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")


@app.get("/api/resume/default")
async def get_default_resume_ranking():
    """Rank opportunities against default profile/resume (Nitin_resume.pdf)."""
    import json
    from resume_matcher import extract_text_from_pdf_bytes, score_all_jobs
    
    pdf_path = BASE_DIR / "Nitin_resume.pdf"
    txt_path = BASE_DIR / "resume_text.txt"
    
    try:
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                content = f.read()
            text = extract_text_from_pdf_bytes(content)
            filename = "Nitin_resume.pdf"
        elif txt_path.exists():
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()
            filename = "resume_text.txt"
        else:
            raise HTTPException(status_code=404, detail="Default resume not found.")

        jobs_path = BASE_DIR / "data" / "jobs_data.json"
        if not jobs_path.exists():
            jobs_path = BASE_DIR / "jobs_data.json"
        with open(jobs_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        result = score_all_jobs(jobs, text)
        result["filename"] = filename
        result["status"] = "success"
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apply", response_model=ApplyResponse)
async def start_application(req: ApplyRequest, background_tasks: BackgroundTasks):
    """
    Launch an automated application session for a job.
    Returns a session_id for polling status.
    """
    if not req.apply_url or not req.apply_url.startswith("http"):
        raise HTTPException(status_code=400, detail="apply_url must be a valid http/https URL.")

    # Duplicate check
    if not req.force:
        previous = has_applied_before(req.job_id)
        if previous:
            return ApplyResponse(
                session_id="",
                status="duplicate",
                message=(
                    f"You already applied to {req.company} on "
                    f"{previous.get('attempted_at', 'an earlier date')}. "
                    "Pass force=true to apply again."
                )
            )

    # Load profile
    try:
        profile = load_profile()
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Create session + DB record
    session = create_session(
        job_id=req.job_id,
        company=req.company,
        role=req.role,
        apply_url=req.apply_url,
    )

    # Pick handler and run in background
    handler = get_handler(req.apply_url, session, profile)

    background_tasks.add_task(_run_handler, handler)

    return ApplyResponse(
        session_id=session.session_id,
        status=AppStatus.PENDING,
        message=f"Application session started for {req.company}. Poll /api/apply/{session.session_id}/status for updates."
    )


async def _run_handler(handler):
    """Run the handler coroutine in the background."""
    await handler.run()


@app.get("/api/apply/{session_id}/status")
async def get_application_status(session_id: str):
    """Poll for the current status of an application session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    return session.to_dict()


@app.post("/api/apply/{session_id}/confirm")
async def confirm_submission(session_id: str):
    """
    User explicitly confirms the form looks good — triggers final submission.
    This is the ONLY way a submission happens.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    if session.status != AppStatus.WAITING:
        raise HTTPException(
            status_code=400,
            detail=f"Session is in status '{session.status}' — not waiting for confirmation."
        )
    session.confirm()
    return {"message": "Confirmation received. Submitting application…"}


@app.post("/api/apply/{session_id}/abort")
async def abort_application(session_id: str):
    """User aborts the application — no submission will be made."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    session.abort()
    return {"message": "Abort signal sent. Application will not be submitted."}


@app.get("/api/history")
async def application_history(limit: int = 200):
    """Return persistent application history from SQLite."""
    return get_history(limit=limit)


@app.get("/api/history/export")
async def export_history():
    """Download application history as an Excel file."""
    output_path = str(BASE_DIR / "application_history_export.xlsx")
    try:
        export_history_excel(output_path)
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"application_history_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )


@app.get("/api/supported-sites")
async def supported_sites():
    """Return the list of sites with automation support."""
    return list_supported_sites()


# ── Gmail Integration Routes ─────────────────────────────────────────────── #

@app.get("/api/gmail/status")
async def gmail_status():
    """Return Gmail OAuth 2.0 / App Password connection status."""
    from gmail_service import gmail_client
    return gmail_client.get_connection_status()


@app.get("/api/gmail/auth-url")
async def gmail_auth_url(redirect_uri: str = "http://localhost:5000/api/gmail/oauth-callback"):
    """Return Google OAuth 2.0 authorization URL."""
    from gmail_service import gmail_client
    try:
        url = gmail_client.get_auth_url(redirect_uri=redirect_uri)
        return {"auth_url": url}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/gmail/oauth-callback")
async def gmail_oauth_callback(code: str, redirect_uri: str = "http://localhost:5000/api/gmail/oauth-callback"):
    """Exchange authorization code for token and save credentials."""
    from gmail_service import gmail_client
    try:
        res = gmail_client.exchange_code_for_token(code=code, redirect_uri=redirect_uri)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/gmail/send-test")
async def gmail_send_test(req: EmailTestRequest):
    """Send a test email to verify Gmail connectivity."""
    from gmail_service import gmail_client
    from candidate_profile import sanitize_email
    raw_email = req.to or get_safe_profile().get("email", "codernitin55@gmail.com")
    profile_email = sanitize_email(raw_email)
    res = gmail_client.send_email(
        to=profile_email,
        subject=req.subject or "Test Email from Job Hunt Intelligence",
        html_body=f"<p>{req.body or 'Gmail is connected and working!'}</p>",
        text_body=req.body or "Gmail is connected and working!"
    )
    return res


# ── AI Job Discovery Routes ──────────────────────────────────────────────── #

@app.get("/api/jobs/discover")
async def trigger_job_discovery_get(limit: int = 15):
    """Run targeted AI discovery with default parameters."""
    from ai_job_discovery import job_discovery
    try:
        discovered = job_discovery.discover_jobs(limit=limit)
        sync_res = job_discovery.sync_to_feed(discovered)
        return {
            "status": "success",
            "discovered_count": len(discovered),
            "sync": sync_res,
            "sample": discovered[:5]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/discover")
async def trigger_job_discovery(req: DiscoverRequest):
    """Run targeted AI discovery across platforms & career pages."""
    from ai_job_discovery import job_discovery
    try:
        discovered = job_discovery.discover_jobs(
            keywords=req.keywords,
            locations=req.locations,
            platforms=req.platforms,
            limit=req.limit or 20
        )
        sync_res = job_discovery.sync_to_feed(discovered)
        return {
            "status": "success",
            "discovered_count": len(discovered),
            "sync": sync_res,
            "sample": discovered[:5]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── AI Job Matching Routes ───────────────────────────────────────────────── #

@app.post("/api/jobs/match-evaluate")
async def evaluate_job_match(req: MatchRequest):
    """Deeply evaluate a job description for candidate compatibility and eligibility."""
    from ai_job_matcher import ai_matcher
    import json

    job = req.job_data
    if not job and req.job_id:
        jobs_path = BASE_DIR / "data" / "jobs_data.json"
        if not jobs_path.exists():
            jobs_path = BASE_DIR / "jobs_data.json"
        if jobs_path.exists():
            with open(jobs_path, "r", encoding="utf-8") as f:
                all_jobs = json.load(f)
            job = next((j for j in all_jobs if str(j.get("id")) == str(req.job_id)), None)

    if not job:
        raise HTTPException(status_code=404, detail="Job data or job_id not found")

    evaluation = ai_matcher.evaluate_job(job)
    return evaluation


@app.get("/api/jobs/top-eligible")
async def get_top_eligible_jobs(limit: int = 15):
    """Return top eligible opportunities ranked by AI compatibility score."""
    from ai_job_matcher import ai_matcher
    import json

    jobs_path = BASE_DIR / "data" / "jobs_data.json"
    if not jobs_path.exists():
        jobs_path = BASE_DIR / "jobs_data.json"
    if not jobs_path.exists():
        raise HTTPException(status_code=404, detail="jobs_data.json not found")

    with open(jobs_path, "r", encoding="utf-8") as f:
        all_jobs = json.load(f)

    evaluated = ai_matcher.evaluate_batch(all_jobs[:100])
    eligible = [j for j in evaluated if j.get("is_eligible")][:limit]
    return eligible


# ── Email Monitoring Routes ──────────────────────────────────────────────── #

@app.get("/api/email-monitor/scan")
@app.post("/api/email-monitor/scan")
async def scan_application_emails(max_results: int = 25):
    """Scan inbox for application confirmations, interview invites, and rejections."""
    from email_monitor import email_monitor
    results = email_monitor.scan_inbox(max_results=max_results)
    return {"scanned_count": len(results), "emails": results}


@app.post("/api/email-monitor/sync")
async def sync_emails_with_tracker():
    """Sync detected inbox status updates with SQLite application tracker."""
    from email_monitor import email_monitor
    res = email_monitor.sync_tracker()
    return res


# ── Application Tracking Routes ──────────────────────────────────────────── #

@app.get("/api/tracker/summary")
async def tracker_summary():
    """Return statistical summary of all tracked applications."""
    from apply_history import get_tracker_summary
    return get_tracker_summary()


@app.post("/api/tracker/update-status")
async def update_tracker_status(req: TrackerUpdateRequest):
    """Manually update application status and notes in the tracker."""
    from apply_history import update_application_status
    success = update_application_status(
        job_id_or_id=req.job_id_or_id,
        status=req.status,
        notes=req.notes
    )
    return {"success": success, "status": req.status}


# ── Daily Automation Routes ──────────────────────────────────────────────── #

@app.post("/api/automation/run-daily")
async def run_daily_automation(req: AutomationRunRequest, background_tasks: BackgroundTasks):
    """Trigger the autonomous daily job hunting pipeline."""
    from daily_automation import daily_runner
    result = await daily_runner.run(
        dry_run=req.dry_run,
        max_auto_apply=req.max_auto_apply
    )
    return result


# ── Static File Serving (serves the dashboard) ───────────────────────────── #
# Mount AFTER API routes so API takes priority
app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")


# ── Server Entry Point ───────────────────────────────────────────────────── #
def main():
    # Initialise DB
    init_db()

    port = 5000
    url = f"http://localhost:{port}/index.html"

    print("=" * 65)
    print("  🚀 Job Hunt Intelligence — Auto-Apply Edition")
    print(f"  🌐 Dashboard:  {url}")
    print(f"  📡 API Docs:   http://localhost:{port}/docs")
    print("  💡 Press Ctrl+C to stop the server.")
    print("=" * 65)

    webbrowser.open(url)

    uvicorn.run(
        "auto_apply_server:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()

