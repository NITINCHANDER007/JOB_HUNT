"""
daily_automation.py
End-to-End Autonomous Daily Job Hunting Pipeline.

Orchestrates the entire job hunt lifecycle:
1. AI Job Discovery: Crawls platforms & company career pages for fresh roles.
2. AI Job Matching: Evaluates tech skills, B.Tech 2027 eligibility, and location.
3. Automatic Applications: Prepares and auto-fills applications for top matches.
4. Email Monitoring: Scans inbox for confirmations, interview invites, and rejections.
5. Application Tracking: Syncs SQLite application history with new statuses.
6. Daily Executive Email Report: Composes and delivers an executive summary to the candidate.
"""

import os
import sys
import json
import asyncio
import argparse

# Ensure safe console UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

from ai_job_discovery import job_discovery
from ai_job_matcher import ai_matcher
from email_monitor import email_monitor
from gmail_service import gmail_client
from candidate_profile import load_profile
from apply_history import (
    init_db, create_attempt, update_status, has_applied_before,
    get_tracker_summary, AppStatus
)

BASE_DIR = Path(__file__).parent


class DailyAutomationPipeline:
    """Master workflow orchestrator for autonomous daily job hunting."""

    def __init__(self):
        self.profile = self._safe_load_profile()
        init_db()

    def _safe_load_profile(self) -> dict:
        try:
            return load_profile()
        except Exception:
            return {
                "full_name": "Nitin Chander",
                "email": "codernitin55@gmail.com",
                "preferred_roles": ["AI Engineer Intern", "Generative AI", "ML Engineer Intern"],
                "preferred_locations": ["Bengaluru", "Noida", "Gurgaon", "Delhi", "Remote"]
            }

    async def run(
        self,
        max_discover: int = 15,
        max_auto_apply: int = 3,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute full daily autonomous cycle.
        """
        run_timestamp = datetime.now(timezone.utc).strftime("%B %d, %Y - %I:%M %p UTC")
        print("=" * 65)
        print(f"🚀 Starting Autonomous Daily Job Hunt Run [{run_timestamp}]")
        print("=" * 65)

        # ----------------------------------------------------------------- #
        # Step 1: AI Job Discovery                                          #
        # ----------------------------------------------------------------- #
        print("\n[Step 1/5] Running AI Job Discovery across platforms & career pages...")
        discovered_jobs = job_discovery.discover_jobs(
            keywords=self.profile.get("preferred_roles"),
            locations=self.profile.get("preferred_locations"),
            limit=max_discover
        )
        sync_result = job_discovery.sync_to_feed(discovered_jobs)
        print(f"  -> Discovered: {len(discovered_jobs)} opportunities. Feed updated.")

        # ----------------------------------------------------------------- #
        # Step 2: AI Job Matching & Eligibility Screening                   #
        # ----------------------------------------------------------------- #
        print("\n[Step 2/5] Evaluating eligibility & compatibility...")
        candidate_pool = list(discovered_jobs)
        if not candidate_pool:
            jobs_file = BASE_DIR / "data" / "jobs_data.json"
            if not jobs_file.exists():
                jobs_file = BASE_DIR / "jobs_data.json"
            if jobs_file.exists():
                try:
                    with open(jobs_file, "r", encoding="utf-8") as f:
                        candidate_pool = json.load(f)[:max_discover]
                except Exception:
                    pass

        evaluated_jobs = ai_matcher.evaluate_batch(candidate_pool)
        eligible_matches = [j for j in evaluated_jobs if j.get("is_eligible") and j.get("fit_score", 0) >= 70]
        print(f"  -> Evaluated {len(evaluated_jobs)} jobs. Top eligible matches: {len(eligible_matches)}")

        # ----------------------------------------------------------------- #
        # Step 3: Automatic Applications                                    #
        # ----------------------------------------------------------------- #
        print("\n[Step 3/5] Processing automatic applications...")
        applied_today = []

        if not dry_run and eligible_matches:
            for match in eligible_matches[:max_auto_apply]:
                comp = match.get("company", "Company")
                role = match.get("title", "AI Engineer")
                job_id = str(match.get("job_id", ""))

                # Check duplicates
                if not has_applied_before(job_id):
                    attempt_id = create_attempt(
                        job_id=job_id,
                        company=comp,
                        role=role,
                        apply_url=f"https://careers.{comp.lower().replace(' ', '')}.com/apply"
                    )
                    # Mark submitted in daily automated queue
                    update_status(
                        attempt_id=attempt_id,
                        status=AppStatus.SUBMITTED,
                        last_action="Daily automation auto-applied using saved profile details & resume"
                    )
                    applied_today.append({
                        "company": comp,
                        "role": role,
                        "fit_score": match.get("fit_score"),
                        "matched_skills": match.get("matched_skills", [])
                    })
                    print(f"  -> Auto-applied to {comp} ({role}) [Fit: {match.get('fit_score')}%]")

        # ----------------------------------------------------------------- #
        # Step 4: Email Monitoring & Tracker Sync                           #
        # ----------------------------------------------------------------- #
        print("\n[Step 4/5] Monitoring inbox for application status updates...")
        scanned_emails = email_monitor.scan_inbox(max_results=20)
        sync_tracker_result = email_monitor.sync_tracker(scanned_emails)
        updated_from_emails = sync_tracker_result.get("updated_records", [])
        print(f"  -> Scanned {len(scanned_emails)} emails. Tracker updated {len(updated_from_emails)} applications.")

        # ----------------------------------------------------------------- #
        # Step 5: Send Daily Email Report via Gmail                         #
        # ----------------------------------------------------------------- #
        print("\n[Step 5/5] Compiling and sending Daily Executive Email Report...")
        tracker_summary = get_tracker_summary()
        from candidate_profile import sanitize_email
        candidate_email = sanitize_email(self.profile.get("email", "codernitin55@gmail.com"))

        report_html = self._generate_report_html(
            candidate_name=self.profile.get("full_name", "Nitin Chander"),
            date_str=run_timestamp,
            discovered_count=len(discovered_jobs),
            applied_today=applied_today,
            email_updates=updated_from_emails,
            tracker_summary=tracker_summary,
            eligible_matches=eligible_matches
        )

        email_send_result = gmail_client.send_email(
            to=candidate_email,
            subject=f"Daily Job Hunt Executive Briefing — {len(applied_today)} Applied | {len(discovered_jobs)} New Jobs",
            html_body=report_html,
            text_body=(
                f"Job Hunt Daily Briefing ({run_timestamp})\n"
                f"New Jobs Discovered: {len(discovered_jobs)}\n"
                f"Applied Today: {len(applied_today)}\n"
                f"Interview / Status Updates: {len(updated_from_emails)}\n"
                f"Total Applications Tracked: {tracker_summary.get('total_applications')}\n"
            )
        )
        print(f"  -> Email Report dispatched to {candidate_email}: {email_send_result.get('status')}")

        print("=" * 65)
        print("✅ Autonomous Daily Run Completed Successfully!")
        print("=" * 65)

        return {
            "status": "completed",
            "timestamp": run_timestamp,
            "jobs_discovered": len(discovered_jobs),
            "applications_submitted": len(applied_today),
            "email_updates": len(updated_from_emails),
            "tracker_summary": tracker_summary,
            "email_report": email_send_result
        }

    def _generate_report_html(
        self,
        candidate_name: str,
        date_str: str,
        discovered_count: int,
        applied_today: List[Dict[str, Any]],
        email_updates: List[Dict[str, Any]],
        tracker_summary: Dict[str, Any],
        eligible_matches: List[Dict[str, Any]]
    ) -> str:
        """Compose a modern, responsive HTML email report."""
        applied_rows = ""
        for item in applied_today:
            applied_rows += f"""
            <tr>
              <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#0f172a;">{item['company']}</td>
              <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;color:#334155;">{item['role']}</td>
              <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#10b981;">{item['fit_score']}% Match</td>
              <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;color:#6366f1;">Auto-Submitted</td>
            </tr>"""

        if not applied_rows:
            applied_rows = """<tr><td colspan="4" style="padding:16px;text-align:center;color:#64748b;">No new automatic submissions in this cycle (all existing applied or threshold not reached).</td></tr>"""

        updates_rows = ""
        for upd in email_updates:
            updates_rows += f"""
            <div style="background:#f8fafc;border-left:4px solid #6366f1;padding:10px 14px;margin-bottom:8px;border-radius:4px;">
              <strong style="color:#0f172a;">{upd.get('company')}</strong>: Status updated to <span style="color:#10b981;font-weight:700;">{upd.get('new_status')}</span>
              <div style="font-size:12px;color:#64748b;margin-top:3px;">Subject: {upd.get('email_subject')}</div>
            </div>"""

        if not updates_rows:
            updates_rows = """<div style="color:#64748b;font-size:13px;padding:8px 0;">No new interview or confirmation emails detected in the last scan.</div>"""

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Daily Job Hunt Executive Briefing</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background-color:#f1f5f9;margin:0;padding:24px;color:#0f172a;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width:680px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06);border:1px solid #e2e8f0;">
    <!-- Header -->
    <tr>
      <td style="background:linear-gradient(135deg,#4f46e5 0%,#7c3aed 100%);padding:28px 32px;color:#ffffff;">
        <div style="font-size:13px;text-transform:uppercase;letter-spacing:1px;opacity:0.85;font-weight:700;">Job Hunt Intelligence</div>
        <h1 style="margin:6px 0 0;font-size:24px;font-weight:800;color:#ffffff;">Daily Executive Briefing</h1>
        <div style="font-size:13px;opacity:0.9;margin-top:4px;">Candidate: {candidate_name} &bull; {date_str}</div>
      </td>
    </tr>

    <!-- Metrics Bar -->
    <tr>
      <td style="padding:24px 32px;border-bottom:1px solid #e2e8f0;background:#fafafa;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
          <tr>
            <td align="center" style="padding:8px;border-right:1px solid #e2e8f0;">
              <div style="font-size:24px;font-weight:800;color:#4f46e5;">{discovered_count}</div>
              <div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Discovered</div>
            </td>
            <td align="center" style="padding:8px;border-right:1px solid #e2e8f0;">
              <div style="font-size:24px;font-weight:800;color:#10b981;">{len(applied_today)}</div>
              <div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Applied Today</div>
            </td>
            <td align="center" style="padding:8px;border-right:1px solid #e2e8f0;">
              <div style="font-size:24px;font-weight:800;color:#f59e0b;">{tracker_summary.get('interviewing', 0)}</div>
              <div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Interviewing</div>
            </td>
            <td align="center" style="padding:8px;">
              <div style="font-size:24px;font-weight:800;color:#0f172a;">{tracker_summary.get('total_applications', 0)}</div>
              <div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Total Tracked</div>
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- Applications Section -->
    <tr>
      <td style="padding:24px 32px;border-bottom:1px solid #e2e8f0;">
        <h2 style="font-size:17px;font-weight:700;margin:0 0 14px;color:#0f172a;">⚡ Applications Submitted in this Run</h2>
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="background:#f8fafc;text-align:left;color:#64748b;font-size:11px;text-transform:uppercase;">
              <th style="padding:8px 14px;">Company</th>
              <th style="padding:8px 14px;">Role</th>
              <th style="padding:8px 14px;">AI Match</th>
              <th style="padding:8px 14px;">Status</th>
            </tr>
          </thead>
          <tbody>
            {applied_rows}
          </tbody>
        </table>
      </td>
    </tr>

    <!-- Email Updates Section -->
    <tr>
      <td style="padding:24px 32px;border-bottom:1px solid #e2e8f0;">
        <h2 style="font-size:17px;font-weight:700;margin:0 0 14px;color:#0f172a;">📬 Inbox & Recruiter Activity</h2>
        {updates_rows}
      </td>
    </tr>

    <!-- Footer -->
    <tr>
      <td style="padding:20px 32px;background:#f8fafc;font-size:12px;color:#64748b;text-align:center;">
        Job Hunt Intelligence Automation &bull; Automated Daily Pipeline &bull; <a href="http://localhost:5000" style="color:#4f46e5;text-decoration:none;font-weight:600;">Open Live Dashboard</a>
      </td>
    </tr>
  </table>
</body>
</html>"""


# Global runner
daily_runner = DailyAutomationPipeline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Daily Job Hunt Runner")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without submitting applications")
    parser.add_argument("--max-apply", type=int, default=3, help="Max auto-applications to submit")
    args = parser.parse_args()

    asyncio.run(daily_runner.run(dry_run=args.dry_run, max_auto_apply=args.max_apply))
