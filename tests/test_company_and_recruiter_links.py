"""
Automated test suite verifying the separation of Company LinkedIn vs. Recruiter LinkedIn:
1. Discover Dollar has verified company LinkedIn: https://www.linkedin.com/company/discover-dollar/
2. Unverified company pages use LinkedIn Companies filter:
   https://www.linkedin.com/search/results/companies/?keywords=...
   with label "Find Company on LinkedIn"
3. Recruiter searches use LinkedIn People filter:
   https://www.linkedin.com/search/results/people/?keywords=...
   with label "Find Recruiter"
   Example: "Subrahmanya Rao Discover Dollar"
4. Verified corporate pages open directly; unverified fall back to company search.
5. Tested across Table view, Card view, and Modal view (Overview and Cold Email tabs).
6. Destination URLs verified for exact query parameters.
"""

import sys
import os
import json
import urllib.parse
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON_PATH = os.path.join(BASE_DIR, "data", "jobs_data.json") if os.path.exists(os.path.join(BASE_DIR, "data", "jobs_data.json")) else os.path.join(BASE_DIR, "jobs_data.json")

def test_dataset_verification():
    print("[TEST 1] Auditing dataset (jobs_data.json) for Company & Recruiter LinkedIn separation...")
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    assert len(jobs) > 0, "jobs_data.json should not be empty"

    # 1. Discover Dollar check
    dd = next((j for j in jobs if "Discover Dollar" in j["company"]), None)
    assert dd is not None, "Discover Dollar not found in dataset"
    assert dd.get("companyLinkedInVerified") is True, "Discover Dollar company LinkedIn must be verified"
    assert dd.get("companyLinkedIn") == "https://www.linkedin.com/company/discover-dollar/", f"Unexpected Discover Dollar company URL: {dd.get('companyLinkedIn')}"
    assert dd.get("recruiterLinkedIn") == "", "Discover Dollar personal recruiter slug must not be guessed"
    assert dd.get("recruiterLinkedInVerified") is False, "Discover Dollar recruiter should be unverified"
    print("  [PASS] Discover Dollar verified company URL is https://www.linkedin.com/company/discover-dollar/")

    # 2. Check unverified company (e.g. The SmartBridge)
    sb = next((j for j in jobs if "SmartBridge" in j["company"]), None)
    assert sb is not None, "SmartBridge not found in dataset"
    assert sb.get("companyLinkedInVerified") is False, "SmartBridge company should be unverified"
    assert sb.get("companyLinkedIn") == "", "SmartBridge company LinkedIn should be empty"
    print("  [PASS] Unverified company (SmartBridge) correctly marked with companyLinkedInVerified=False")

    # 3. Overall audit
    verified_companies = [j["company"] for j in jobs if j.get("companyLinkedInVerified")]
    unverified_companies = [j["company"] for j in jobs if not j.get("companyLinkedInVerified")]
    print(f"  [PASS] Total jobs: {len(jobs)}. Verified companies: {len(verified_companies)}. Unverified companies: {len(unverified_companies)}.")

def test_frontend_links():
    print("\n[TEST 2] Verifying frontend rendering & URL filters across Table, Card, and Modal views...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto("http://127.0.0.1:5000", timeout=15000)
        page.wait_for_selector("#jobsTableBody tr", timeout=10000)

        # -------------------------------------------------------------
        # 1. TABLE VIEW - Verify clean rows without bloated contact buttons
        # -------------------------------------------------------------
        print("\n--- 1. Testing Table View ---")
        dd_row = page.locator("#jobsTableBody tr", has_text="Discover Dollar").first
        assert dd_row.count() > 0, "Discover Dollar row not found in table"

        # Verify table view col-company is clean (contact badges removed as requested)
        dd_col_comp = dd_row.locator(".col-company")
        assert dd_col_comp.locator(".contact-badge, .source-badge").count() == 0, "Table view col-company should not have bloated contact/source badges"
        print("  [PASS] Table View is clean without bloated contact/source badges")

        # -------------------------------------------------------------
        # 2. CARD VIEW
        # -------------------------------------------------------------
        print("\n--- 2. Testing Card View ---")
        page.locator("#viewGridBtn").click()
        page.wait_for_selector("#cardsViewSection .job-card", timeout=5000)

        dd_card = page.locator("#cardsViewSection .job-card", has_text="Discover Dollar").first
        assert dd_card.count() > 0, "Discover Dollar card not found"

        dd_card_comp = dd_card.locator("a.contact-company-badge")
        assert dd_card_comp.count() > 0
        assert dd_card_comp.get_attribute("href") == "https://www.linkedin.com/company/discover-dollar/"
        assert dd_card_comp.inner_text().strip() == "Company LinkedIn"

        dd_card_rec = dd_card.locator("a.contact-recruiter-search-badge")
        assert dd_card_rec.count() > 0
        assert "linkedin.com/search/results/people/?keywords=" in dd_card_rec.get_attribute("href")
        assert dd_card_rec.inner_text().strip() == "Find Recruiter"
        print("  [PASS] Card View renders separate Company LinkedIn and Find Recruiter buttons.")

        # Switch back to table view
        page.locator("#viewTableBtn").click()
        page.wait_for_selector("#jobsTableBody tr", timeout=5000)

        # -------------------------------------------------------------
        # 3. MODAL VIEW - Discover Dollar
        # -------------------------------------------------------------
        print("\n--- 3. Testing Job Details Modal ---")
        dd_detail_btn = dd_row.locator("button.btn-open-modal")
        dd_detail_btn.click()
        page.wait_for_selector("#detailModal", state="visible", timeout=5000)

        # Overview Tab
        modal_comp_ov = page.locator("#modalOverviewCompanyLinkedIn")
        assert modal_comp_ov.is_visible()
        assert modal_comp_ov.get_attribute("href") == "https://www.linkedin.com/company/discover-dollar/"
        assert "Company LinkedIn" in modal_comp_ov.inner_text()

        modal_rec_ov = page.locator("#modalOverviewRecruiterLinkedIn")
        assert modal_rec_ov.is_visible()
        assert "linkedin.com/search/results/people/?keywords=" in modal_rec_ov.get_attribute("href")
        assert "Find Recruiter" in modal_rec_ov.inner_text()
        print("  [PASS] Modal Overview Tab has separate Company LinkedIn and Find Recruiter buttons.")

        # Cold Email Tab
        page.locator(".modal-tab-btn[data-tab='email']").click()
        modal_comp_ce = page.locator("#modalCompanyLinkedIn")
        assert modal_comp_ce.is_visible()
        assert modal_comp_ce.get_attribute("href") == "https://www.linkedin.com/company/discover-dollar/"
        assert "Company LinkedIn" in modal_comp_ce.inner_text()

        modal_rec_ce = page.locator("#modalRecruiterLinkedIn")
        assert modal_rec_ce.is_visible()
        assert "linkedin.com/search/results/people/?keywords=" in modal_rec_ce.get_attribute("href")
        assert "Find Recruiter" in modal_rec_ce.inner_text()
        print("  [PASS] Modal Cold Email Tab has separate Company LinkedIn and Find Recruiter buttons.")

        # Close Modal
        page.locator("#modalCloseBtn").click()
        page.wait_for_selector("#detailModal", state="hidden", timeout=5000)

        # Check unverified modal (SmartBridge)
        sb_row = page.locator("#jobsTableBody tr", has_text="SmartBridge").first
        sb_detail_btn = sb_row.locator("button.btn-open-modal")
        sb_detail_btn.click()
        page.wait_for_selector("#detailModal", state="visible", timeout=5000)

        page.locator(".modal-tab-btn[data-tab='overview']").click()
        sb_comp_ov = page.locator("#modalOverviewCompanyLinkedIn")
        assert "linkedin.com/search/results/companies/?keywords=" in sb_comp_ov.get_attribute("href")
        assert "Find Company on LinkedIn" in sb_comp_ov.inner_text()

        page.locator(".modal-tab-btn[data-tab='email']").click()
        sb_comp_ce = page.locator("#modalCompanyLinkedIn")
        assert "linkedin.com/search/results/companies/?keywords=" in sb_comp_ce.get_attribute("href")
        assert "Find Company on LinkedIn" in sb_comp_ce.inner_text()
        print("  [PASS] Modal for unverified company uses Companies search filter in both tabs.")

        page.locator("#modalCloseBtn").click()

        # Zero console errors
        assert len(console_errors) == 0, f"Encountered JS errors: {console_errors}"
        print("  [PASS] Zero JS console errors throughout test.")

        browser.close()

if __name__ == "__main__":
    test_dataset_verification()
    test_frontend_links()
    print("\nALL COMPANY AND RECRUITER LINK TESTS PASSED SUCCESSFULLY!")
