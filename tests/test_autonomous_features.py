"""
tests/test_autonomous_features.py
Comprehensive Verification Suite for the 7 Autonomous Job Hunt Features:
1. Gmail Integration (OAuth 2.0 / status / send-test)
3. AI Job Discovery (platforms + career pages)
4. AI Job Matching (skills, B.Tech 2027 eligibility, gaps)
5. Automatic Applications (SmartFormFiller + SmartApplyHandler)
6. Email Monitoring (confirmations, interviews, rejections)
7. Application Tracking (tracker summary, status transitions)
8. Daily Automation (end-to-end pipeline run)
"""

import sys
import unittest
import requests
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

API_BASE = "http://127.0.0.1:5000"


class TestAutonomousFeatures(unittest.TestCase):

    # ------------------------------------------------------------- #
    # Feature 1: Gmail Integration                                  #
    # ------------------------------------------------------------- #
    def test_01_gmail_status_and_send(self):
        print("\n--- 1. Testing Gmail Integration ---")
        # Check connection status endpoint
        resp = requests.get(f"{API_BASE}/api/gmail/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("status", data)
        self.assertIn("connected", data)
        print(f"  [PASS] Gmail status endpoint returns 200: {data.get('status')}")

        # Test sending a mock/verified message
        test_payload = {
            "to": "nitinchandra834@gmail.com",
            "subject": "Verification Test Email",
            "body": "Checking Gmail Integration connectivity."
        }
        send_resp = requests.post(f"{API_BASE}/api/gmail/send-test", json=test_payload)
        self.assertEqual(send_resp.status_code, 200)
        send_data = send_resp.json()
        self.assertIn(send_data.get("status"), ["sent", "mock_sent"])
        print(f"  [PASS] Gmail send-test succeeded: delivery method={send_data.get('method')}")

    # ------------------------------------------------------------- #
    # Feature 3: AI Job Discovery                                   #
    # ------------------------------------------------------------- #
    def test_02_ai_job_discovery(self):
        print("\n--- 2. Testing AI Job Discovery ---")
        payload = {
            "keywords": ["AI Engineer", "Generative AI", "Python Developer"],
            "locations": ["Bengaluru", "Noida", "Remote"],
            "platforms": ["LinkedIn", "Indeed", "CareerPage"],
            "limit": 5
        }
        resp = requests.post(f"{API_BASE}/api/jobs/discover", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("discovered_count", data)
        self.assertIn("sync", data)
        print(f"  [PASS] Job Discovery endpoint returns: {data.get('discovered_count')} opportunities")

    # ------------------------------------------------------------- #
    # Feature 4: AI Job Matching & Eligibility                     #
    # ------------------------------------------------------------- #
    def test_03_ai_job_matching(self):
        print("\n--- 3. Testing AI Job Matching & Eligibility ---")
        sample_job = {
            "id": 9991,
            "company": "DeepMind Innovations",
            "title": "Generative AI Intern",
            "location": "Bengaluru, Karnataka",
            "description": "Looking for a GenAI Intern skilled in Python, RAG, LangChain, and FastAPI."
        }
        resp = requests.post(f"{API_BASE}/api/jobs/match-evaluate", json={"job_data": sample_job})
        self.assertEqual(resp.status_code, 200)
        res = resp.json()
        self.assertTrue(res.get("is_eligible"))
        self.assertGreaterEqual(res.get("fit_score", 0), 80)
        self.assertEqual(res.get("fit_tier"), "High")
        self.assertIn("LangChain", res.get("matched_skills", []))
        self.assertIn("Python", res.get("matched_skills", []))
        print(f"  [PASS] AI Matcher Score: {res.get('fit_score')}% | Tier: {res.get('fit_tier')} | Matched: {res.get('matched_skills')}")

        # Test senior role ineligibility
        senior_job = {
            "id": 9992,
            "company": "Enterprise Corp",
            "title": "Senior Staff Director of AI",
            "location": "Bengaluru",
            "description": "Requires 10+ years of leading ML engineering teams."
        }
        s_resp = requests.post(f"{API_BASE}/api/jobs/match-evaluate", json={"job_data": senior_job})
        self.assertEqual(s_resp.status_code, 200)
        s_res = s_resp.json()
        self.assertFalse(s_res.get("is_eligible"))
        print(f"  [PASS] Senior filter correctly flagged role as ineligible: {s_res.get('eligibility_reasons')}")

    # ------------------------------------------------------------- #
    # Feature 5: Automatic Applications & Smart Form Filler        #
    # ------------------------------------------------------------- #
    def test_04_smart_form_filler_handler(self):
        print("\n--- 4. Testing Smart Form Filler Handler ---")
        from apply_engine.handler_registry import get_handler
        from apply_engine.apply_session import create_session

        sess = create_session(
            job_id="test_ats_1",
            company="Ashby Tech",
            role="AI Engineer",
            apply_url="https://jobs.ashbyhq.com/demo/apply"
        )
        handler = get_handler(sess.apply_url, sess, {})
        self.assertEqual(handler.HANDLER_NAME, "smart_apply")
        print(f"  [PASS] ATS career portal correctly assigned handler: {handler.HANDLER_NAME}")

    # ------------------------------------------------------------- #
    # Feature 6: Email Monitoring                                   #
    # ------------------------------------------------------------- #
    def test_05_email_monitoring_classification(self):
        print("\n--- 5. Testing Email Monitoring Classification ---")
        from email_monitor import email_monitor

        # Test Interview
        inv = email_monitor.classify_email(
            subject="Interview Invitation for AI Engineer Intern",
            body="We would love to invite you to an interview round with our tech team.",
            sender="Hiring <recruiting@swiggy.com>"
        )
        self.assertEqual(inv["type"], "INTERVIEW")
        self.assertEqual(inv["company"], "Swiggy")
        print(f"  [PASS] Interview classification accurate: Company={inv['company']}, Type={inv['type']}")

        # Test Rejection
        rej = email_monitor.classify_email(
            subject="Application status update",
            body="Unfortunately, we have decided not to move forward with your application.",
            sender="HR <careers@razorpay.com>"
        )
        self.assertEqual(rej["type"], "REJECTION")
        self.assertEqual(rej["company"], "Razorpay")
        print(f"  [PASS] Rejection classification accurate: Company={rej['company']}, Type={rej['type']}")

        # Test endpoint
        resp = requests.post(f"{API_BASE}/api/email-monitor/scan?max_results=5")
        self.assertEqual(resp.status_code, 200)
        print(f"  [PASS] Email monitor scan endpoint returned 200 OK")

    # ------------------------------------------------------------- #
    # Feature 7: Application Tracking                               #
    # ------------------------------------------------------------- #
    def test_06_application_tracker(self):
        print("\n--- 6. Testing Application Tracking & Analytics ---")
        # Check tracker summary
        resp = requests.get(f"{API_BASE}/api/tracker/summary")
        self.assertEqual(resp.status_code, 200)
        summary = resp.json()
        self.assertIn("total_applications", summary)
        self.assertIn("submitted", summary)
        self.assertIn("response_rate_percent", summary)
        print(f"  [PASS] Tracker Summary: Total={summary.get('total_applications')}, Submitted={summary.get('submitted')}, Response Rate={summary.get('response_rate_percent')}%")

        # Update status
        upd_payload = {
            "job_id_or_id": "test_job_tracker_99",
            "status": "Interviewing",
            "notes": "First round scheduled via Email Monitor"
        }
        upd_resp = requests.post(f"{API_BASE}/api/tracker/update-status", json=upd_payload)
        self.assertEqual(upd_resp.status_code, 200)
        self.assertTrue(upd_resp.json().get("success"))
        print("  [PASS] Application tracker status transition succeeded")

    # ------------------------------------------------------------- #
    # Feature 8: Daily Automation Pipeline                         #
    # ------------------------------------------------------------- #
    def test_07_daily_automation_pipeline(self):
        print("\n--- 7. Testing Daily Automation Pipeline (Dry-Run) ---")
        payload = {
            "dry_run": True,
            "max_auto_apply": 2
        }
        resp = requests.post(f"{API_BASE}/api/automation/run-daily", json=payload)
        self.assertEqual(resp.status_code, 200)
        res = resp.json()
        self.assertEqual(res.get("status"), "completed")
        self.assertIn("jobs_discovered", res)
        self.assertIn("email_report", res)
        print(f"  [PASS] Daily Automation completed cycle: Jobs Discovered={res.get('jobs_discovered')}, Email Dispatched={res.get('email_report', {}).get('status')}")


if __name__ == "__main__":
    unittest.main()
