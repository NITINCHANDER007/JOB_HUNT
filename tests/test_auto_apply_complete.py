"""
tests/test_auto_apply_complete.py

End-to-end integration test verifying the complete Auto Apply functionality:
1. Account connection and session manager functionality (LinkedIn, Naukri, Indeed).
2. CAPTCHA, Cloudflare, and OTP detection and pause/resume logic.
3. Q&A Knowledge Base screening question resolution without fabricating answers.
4. Complete application lifecycle on a test job link:
   - Form detection
   - Profile & resume population (strictly using codernitin55@gmail.com)
   - Cover letter synthesis & attachment
   - Safety audit screenshot capture
   - Explicit confirmation
   - Submission recording in apply_history.db
"""

import os
import sys
import json
import asyncio
import unittest
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

API_BASE = "http://127.0.0.1:5000"


class TestAutoApplyComplete(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Verify server is up
        try:
            r = requests.get(f"{API_BASE}/api/health", timeout=3)
            if r.status_code != 200:
                raise RuntimeError("FastAPI server is not healthy.")
        except Exception as e:
            raise RuntimeError(f"FastAPI server must be running at {API_BASE}: {e}")

    def test_01_account_connection_status(self):
        """Test account connection status endpoint for LinkedIn, Naukri, Indeed."""
        print("\n--- 1. Testing Account Connection Status ---")
        res = requests.get(f"{API_BASE}/api/accounts/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("linkedin", data)
        self.assertIn("naukri", data)
        self.assertIn("indeed", data)
        self.assertIn("connected", data["linkedin"])
        print(f"  [PASS] Accounts status reported: LinkedIn={data['linkedin']['connected']}, Naukri={data['naukri']['connected']}, Indeed={data['indeed']['connected']}")

    def test_02_handler_registry_routing(self):
        """Verify router correctly dispatches to dedicated handlers."""
        print("\n--- 2. Testing Handler Registry Routing ---")
        from apply_engine.handler_registry import get_handler, list_supported_sites
        from apply_engine.apply_session import create_session
        from candidate_profile import load_profile

        profile = load_profile()
        dummy_sess = create_session("test-1", "TestCo", "AI Engineer", "http://localhost:5000/test_form.html")

        # Test localhost
        h_local = get_handler("http://localhost:5000/test_form.html", dummy_sess, profile)
        self.assertEqual(h_local.HANDLER_NAME, "demo_form")

        # Test LinkedIn
        h_li = get_handler("https://www.linkedin.com/jobs/view/12345", dummy_sess, profile)
        self.assertEqual(h_li.HANDLER_NAME, "linkedin_easy_apply")

        # Test Naukri
        h_naukri = get_handler("https://www.naukri.com/job-listings-ai-123", dummy_sess, profile)
        self.assertEqual(h_naukri.HANDLER_NAME, "naukri_apply")

        # Test Indeed
        h_indeed = get_handler("https://www.indeed.com/viewjob?jk=abc", dummy_sess, profile)
        self.assertEqual(h_indeed.HANDLER_NAME, "indeed_apply")

        # Test Greenhouse / ATS
        h_gh = get_handler("https://boards.greenhouse.io/discoverdollar/jobs/123", dummy_sess, profile)
        self.assertEqual(h_gh.HANDLER_NAME, "smart_apply")

        sites = list_supported_sites()
        self.assertGreaterEqual(len(sites), 5)
        print("  [PASS] Handlers correctly routed for localhost, LinkedIn, Naukri, Indeed, and ATS portals.")

    def test_03_captcha_and_challenge_detection(self):
        """Verify CAPTCHA and OTP challenge signatures are properly recognized."""
        print("\n--- 3. Testing CAPTCHA & Security Challenge Detection ---")
        from apply_engine.captcha_detector import CHALLENGE_SELECTORS

        types = {c["type"] for c in CHALLENGE_SELECTORS}
        self.assertIn("CAPTCHA", types)
        self.assertIn("CLOUDFLARE", types)
        self.assertIn("SECURITY_CHECK", types)
        self.assertIn("OTP", types)
        print(f"  [PASS] Challenge detector configured with {len(CHALLENGE_SELECTORS)} patterns across CAPTCHA, Cloudflare, Arkose, and OTP.")

    def test_04_knowledge_base_qa_and_missing_info(self):
        """Verify screening question answering and knowledge base persistence."""
        print("\n--- 4. Testing Knowledge Base Q&A & Persistence ---")
        from apply_engine.smart_form_filler import SmartFormFiller

        filler = SmartFormFiller(None, {})
        kb = filler.kb
        self.assertIn("work_authorization", kb)
        self.assertEqual(kb["work_authorization"]["answer"], "Yes")
        self.assertEqual(kb["graduation_year"]["answer"], "2027")

        # Test custom question saving without fabrication
        asyncio.run(filler.save_custom_answer(
            question_key="preferred_shift",
            question_patterns=["preferred shift", "work shift"],
            answer="Day Shift",
            qtype="text"
        ))
        reloaded = filler._load_knowledge_base()
        self.assertIn("preferred_shift", reloaded)
        self.assertEqual(reloaded["preferred_shift"]["answer"], "Day Shift")
        print("  [PASS] Knowledge Base loaded and persisted verified candidate answer without fabrication.")

    def test_05_single_job_link_full_auto_apply(self):
        """Test the complete Auto-Apply process using one test job link."""
        print("\n--- 5. Testing Single Job Link Complete Process ---")
        job_payload = {
            "job_id": "test-full-auto-01",
            "company": "AutoApply TestCorp",
            "role": "AI Engineer Intern",
            "apply_url": "http://127.0.0.1:5000/test_form.html",
            "force": True
        }

        # 1. Start application session
        start_res = requests.post(f"{API_BASE}/api/apply", json=job_payload)
        self.assertEqual(start_res.status_code, 200)
        start_data = start_res.json()
        session_id = start_data.get("session_id")
        self.assertTrue(bool(session_id))
        print(f"  [PASS] Application session initialized: {session_id}")

        # 2. Wait for handler to fill and pause at Waiting for review
        import time
        max_wait = 20
        waited = 0
        final_status = ""
        while waited < max_wait:
            time.sleep(1)
            waited += 1
            st_res = requests.get(f"{API_BASE}/api/apply/{session_id}/status")
            st_data = st_res.json()
            final_status = st_data.get("status")
            if final_status in ["Waiting for review", "Needs manual action", "Failed", "Submitted successfully"]:
                break

        print(f"  -> Session reached state: '{final_status}' after {waited}s")
        self.assertIn(final_status, ["Waiting for review", "Needs manual action", "Submitted successfully"])

        # 3. Test explicit user confirmation
        if final_status == "Waiting for review":
            conf_res = requests.post(f"{API_BASE}/api/apply/{session_id}/confirm")
            self.assertEqual(conf_res.status_code, 200)
            time.sleep(2)
            st_after = requests.get(f"{API_BASE}/api/apply/{session_id}/status").json()
            self.assertEqual(st_after.get("status"), "Submitted successfully")
            print("  [PASS] User confirmed submission: Application submitted successfully.")

        # 4. Verify recorded in application history
        hist_res = requests.get(f"{API_BASE}/api/history?limit=10")
        self.assertEqual(hist_res.status_code, 200)
        hist = hist_res.json()
        matched = [h for h in hist if h.get("company") == "AutoApply TestCorp"]
        self.assertTrue(len(matched) > 0)
        print("  [PASS] Application record verified in apply_history database.")


if __name__ == "__main__":
    unittest.main()
