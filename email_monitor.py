"""
email_monitor.py
Automated Job Application Email Monitoring Engine.

Features:
- Scans Gmail inbox for job application status updates.
- Intelligently classifies emails into:
  - CONFIRMATION: "Thank you for applying", "Application received"
  - INTERVIEW: "Interview invitation", "Coding assessment", "Next round"
  - REJECTION: "Unfortunately", "Not moving forward", "Other candidates"
  - OFFER: "Job offer", "Offer letter"
- Extracts company name, role, and key dates.
- Automatically syncs and updates SQLite application tracker (apply_history.db).
"""

import re
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

from gmail_service import gmail_client
from apply_history import _get_conn, AppStatus, update_status, get_history

BASE_DIR = Path(__file__).parent


class EmailMonitor:
    """Monitors incoming emails to identify application progress."""

    # Classification regex patterns
    PATTERNS = {
        "OFFER": [
            r"\boffer letter\b",
            r"\bjob offer\b",
            r"\bformal offer\b",
            r"\bpleased to offer\b",
            r"\bcongratulations on your offer\b"
        ],
        "INTERVIEW": [
            r"\binterview invitation\b",
            r"\binvitation to interview\b",
            r"\bnext (?:steps?|round)\b",
            r"\bphone screen\b",
            r"\btechnical (?:interview|round|assessment)\b",
            r"\bcoding (?:assessment|test|challenge)\b",
            r"\bhackerrank\b",
            r"\bcodesignal\b",
            r"\bdiscuss your application\b",
            r"\bschedule a call\b",
            r"\bavailability for (?:an? )?interview\b"
        ],
        "REJECTION": [
            r"\bunfortunately\b",
            r"\bnot moving forward\b",
            r"\bother candidates\b",
            r"\bdecided not to proceed\b",
            r"\bwill not be moving forward\b",
            r"\bposition has been filled\b",
            r"\bwish you (?:the best|every success)\b",
            r"\bat this time\b.*\bnot\b"
        ],
        "CONFIRMATION": [
            r"\bthank you for applying\b",
            r"\bthanks for applying\b",
            r"\bapplication received\b",
            r"\bwe(?:'ve| have) received your application\b",
            r"\bapplication confirmation\b",
            r"\bsuccessfully submitted\b",
            r"\bconfirming receipt of\b"
        ]
    }

    def classify_email(self, subject: str, body: str, sender: str) -> Dict[str, Any]:
        """Classify an email's intent and extract company/role references."""
        text = f"{subject} {body}".lower()

        detected_type = "UNCATEGORIZED"
        confidence = 0.0

        for category, patterns in self.PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text):
                    detected_type = category
                    confidence = 0.95 if re.search(pat, subject.lower()) else 0.85
                    break
            if detected_type != "UNCATEGORIZED":
                break

        # Extract Company name
        company = self._extract_company(subject, sender, body)

        # Extract Role
        role = self._extract_role(subject, body)

        return {
            "type": detected_type,
            "confidence": confidence,
            "company": company,
            "role": role,
            "subject": subject,
            "sender": sender
        }

    def _extract_company(self, subject: str, sender: str, body: str) -> str:
        """Heuristic to extract company name from subject or sender."""
        # 1. From subject: e.g. "Application to Discover Dollar" or "at CredHive"
        sub_match = re.search(r"(?:at|to|with|from)\s+([A-Z][a-zA-Z0-9\s]{2,20})(?:[,\-\–\—\.]|$|\sfor|\sregarding)", subject)
        if sub_match:
            cand = sub_match.group(1).strip()
            if cand.lower() not in ["google", "linkedin", "indeed", "naukri", "application", "your"]:
                return cand

        # 2. From sender name: "CredHive Talent Team <talent@credhive.in>"
        sender_name_match = re.search(r"^([^<@]+)", sender)
        if sender_name_match:
            name = sender_name_match.group(1).strip().strip('"').strip("'")
            name = re.sub(r"(?:Talent|Recruiting|Careers|Hiring|HR|Team|Team|via\s+.*)", "", name, flags=re.IGNORECASE).strip()
            if name and len(name) >= 3 and name.lower() not in ["google", "linkedin", "indeed", "naukri"]:
                return name

        # 3. From sender domain: "@discoverdollar.com"
        domain_match = re.search(r"@([a-zA-Z0-9\-]+)\.(?:com|in|co|io|org|net)", sender)
        if domain_match:
            dom = domain_match.group(1)
            if dom.lower() not in ["gmail", "yahoo", "outlook", "hotmail", "linkedin", "indeed", "naukri", "greenhouse", "lever"]:
                return dom.capitalize()

        return "Unknown Company"

    def _extract_role(self, subject: str, body: str) -> str:
        """Extract job title or role from email text."""
        combined = f"{subject} {body}"
        match = re.search(
            r"\b(AI Engineer|ML Engineer|Generative AI Engineer|Data Scientist|Data Engineer|Python Developer|Software Engineer|Backend Developer)(?:\s+Intern(?:ship)?)?\b",
            combined,
            re.IGNORECASE
        )
        if match:
            return match.group(0).strip()
        return "AI/ML Role"

    def scan_inbox(self, max_results: int = 25) -> List[Dict[str, Any]]:
        """
        Query Gmail for recent application status emails.
        Returns classified email records.
        """
        query = "subject:(application OR applied OR interview OR assessment OR status OR offer OR regrettably)"
        emails = gmail_client.fetch_recent_emails(query=query, max_results=max_results)

        results = []
        for em in emails:
            classification = self.classify_email(
                subject=em.get("subject", ""),
                body=em.get("body", "") or em.get("snippet", ""),
                sender=em.get("sender", "")
            )
            if classification["type"] != "UNCATEGORIZED":
                classification["email_id"] = em.get("id")
                classification["date"] = em.get("date")
                classification["snippet"] = em.get("snippet")
                results.append(classification)

        return results

    def sync_tracker(self, scanned_emails: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Sync application tracker (apply_history.db) with detected emails.
        Updates statuses:
          - CONFIRMATION -> 'Applied'
          - INTERVIEW -> 'Interviewing'
          - REJECTION -> 'Rejected'
          - OFFER -> 'Offer'
        """
        if scanned_emails is None:
            scanned_emails = self.scan_inbox()

        if not scanned_emails:
            return {"updated_count": 0, "message": "No new status updates found in emails."}

        updated_records = []
        with _get_conn() as conn:
            # Load active applications
            cur = conn.execute("SELECT id, company, role, status FROM applications")
            apps = [dict(row) for row in cur.fetchall()]

            for email in scanned_emails:
                email_type = email["type"]
                email_comp = email["company"].lower()

                # Map email type to application tracker status
                target_status = None
                if email_type == "CONFIRMATION":
                    target_status = AppStatus.SUBMITTED
                elif email_type == "INTERVIEW":
                    target_status = "Interviewing"
                elif email_type == "REJECTION":
                    target_status = "Rejected"
                elif email_type == "OFFER":
                    target_status = "Offer"

                if not target_status:
                    continue

                # Find matching application in DB
                for app in apps:
                    if app["company"].lower() in email_comp or email_comp in app["company"].lower():
                        # Update status if progressed
                        if app["status"] != target_status:
                            update_status(
                                attempt_id=app["id"],
                                status=target_status,
                                last_action=f"Updated via Email ({email_type}): {email['subject']}",
                                confirmation=email.get("email_id")
                            )
                            updated_records.append({
                                "id": app["id"],
                                "company": app["company"],
                                "role": app["role"],
                                "old_status": app["status"],
                                "new_status": target_status,
                                "email_subject": email["subject"]
                            })
                            break

        return {
            "updated_count": len(updated_records),
            "updated_records": updated_records,
            "scanned_count": len(scanned_emails)
        }


# Singleton
email_monitor = EmailMonitor()

