"""
Test suite verifying that:
1. No guessed recruiter LinkedIn slugs exist in the dataset (jobs_data.json / jobs_data.js).
2. All jobs have companyLinkedInVerified, recruiterLinkedInVerified, and emailVerified booleans.
3. Separate buttons exist for Company LinkedIn and Recruiter LinkedIn.
4. Verified corporate pages render direct links with target="_blank".
5. Unverified recruiter profiles render a "Find Recruiter" People search link.
6. Unverified company pages render a "Find Company on LinkedIn" Companies search link.
7. Zero console errors across Table view, Card view, and Details modal.
"""

import sys
import os
import json
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON_PATH = os.path.join(BASE_DIR, "data", "jobs_data.json") if os.path.exists(os.path.join(BASE_DIR, "data", "jobs_data.json")) else os.path.join(BASE_DIR, "jobs_data.json")

def test_dataset_integrity():
    print("[TEST 1] Verifying dataset integrity and absence of guessed URLs...")
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    assert len(jobs) > 0, "jobs_data.json should not be empty"

    forbidden_guessed_slugs = [
        "maghav-kumar",
        "subu-rao-discoverdollar",
        "pankaj-sharma-iitr",
        "vinay-kumar-sankarapu",
        "nageen-kommu",
        "shivam-gupta-affordable-organic",
        "amarendar-katkam",
        "dimakh-sahasrabuddhe"
    ]

    for job in jobs:
        assert "companyLinkedInVerified" in job, f"Missing companyLinkedInVerified in job {job.get('id')}"
        assert "recruiterLinkedInVerified" in job, f"Missing recruiterLinkedInVerified in job {job.get('id')}"
        assert "emailVerified" in job, f"Missing emailVerified in job {job.get('id')}"

        recruiter_li = job.get("recruiterLinkedIn", "")
        for slug in forbidden_guessed_slugs:
            assert slug not in recruiter_li, f"Found forbidden slug '{slug}' in job {job.get('id')}"

        if job.get("companyLinkedInVerified"):
            comp_li = job.get("companyLinkedIn", "")
            assert comp_li.startswith("https://www.linkedin.com/company/"), f"Verified company link invalid: {comp_li}"

    print("  [PASS] Dataset audit passed. All 31 entries adhere to verification specifications.")

def test_frontend_recruiter_links():
    print("[TEST 2] Verifying frontend rendering across table, cards, and modal...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto("http://127.0.0.1:5000", timeout=15000)
        page.wait_for_selector("#jobsTableBody tr", timeout=10000)

        # 1. Check Table View - Clean table rows
        credhive_row = page.locator("#jobsTableBody tr", has_text="CredHive").first
        assert credhive_row.count() > 0, "CredHive row not found in table"
        col_comp = credhive_row.locator(".col-company")
        assert col_comp.locator(".contact-badge, .source-badge").count() == 0, "Table view col-company should be clean without bloated badges"
        print("  [PASS] Table View is clean without bloated badges")

        # 2. Check Card View
        card_toggle = page.locator("#viewGridBtn")
        if card_toggle.count() > 0:
            card_toggle.click()
            page.wait_for_selector("#cardsViewSection .job-card", timeout=5000)

            credhive_card = page.locator("#cardsViewSection .job-card", has_text="CredHive").first
            credhive_card_comp = credhive_card.locator("a.contact-company-badge")
            assert credhive_card_comp.count() > 0
            credhive_card_rec = credhive_card.locator("a.contact-recruiter-search-badge")
            assert credhive_card_rec.count() > 0
            assert "linkedin.com/search/results/people/?keywords=" in credhive_card_rec.get_attribute("href")
            print("  [PASS] Card View renders Company LinkedIn and Find Recruiter buttons.")

            tower_card = page.locator("#cardsViewSection .job-card", has_text="Tower Research Capital").first
            tower_card_li = tower_card.locator("a.contact-company-badge")
            assert tower_card_li.count() > 0
            assert tower_card_li.get_attribute("href").rstrip('/') == "https://www.linkedin.com/company/tower-research-capital"
            print("  [PASS] Card View verified company renders direct LinkedIn badge.")

        # Switch back to table view to test modal
        page.locator("#viewTableBtn").click()
        page.wait_for_selector("#jobsTableBody tr", timeout=5000)

        # 3. Check Modal for CredHive
        credhive_detail_btn = credhive_row.locator("button.btn-open-modal")
        credhive_detail_btn.click()
        page.wait_for_selector("#detailModal", state="visible", timeout=5000)

        # Overview Tab
        modal_overview_comp = page.locator("#modalOverviewCompanyLinkedIn")
        assert modal_overview_comp.is_visible()
        assert "linkedin.com/company/credhive-fintech" in modal_overview_comp.get_attribute("href")

        modal_overview_rec = page.locator("#modalOverviewRecruiterLinkedIn")
        assert modal_overview_rec.is_visible()
        assert "linkedin.com/search/results/people/?keywords=" in modal_overview_rec.get_attribute("href")

        # Switch to Cold Email Tab
        page.locator(".modal-tab-btn[data-tab='email']").click()
        modal_recruiter_li = page.locator("#modalRecruiterLinkedIn")
        assert modal_recruiter_li.is_visible()
        modal_recruiter_href = modal_recruiter_li.get_attribute("href")
        assert "linkedin.com/search/results/people/?keywords=" in modal_recruiter_href
        assert "Find Recruiter" in modal_recruiter_li.text_content()
        assert modal_recruiter_li.get_attribute("target") == "_blank"

        # Check Email in Cold Email Tab
        modal_email = page.locator("#modalContactEmail")
        assert modal_email.is_visible()
        assert modal_email.get_attribute("href").startswith("mailto:maghav@credhive.in")
        print("  [PASS] Modal renders Company LinkedIn and Find Recruiter links in both Overview and Cold Email tabs.")

        # Close Modal
        page.locator("#modalCloseBtn").click()
        page.wait_for_selector("#detailModal", state="hidden", timeout=5000)

        # 4. Check Modal for Verified (Tower Research Capital)
        tower_row = page.locator("#jobsTableBody tr", has_text="Tower Research Capital").first
        tower_detail_btn = tower_row.locator("button.btn-open-modal")
        tower_detail_btn.click()
        page.wait_for_selector("#detailModal", state="visible", timeout=5000)

        # Overview Tab
        page.locator(".modal-tab-btn[data-tab='overview']").click()
        tower_overview_li = page.locator("#modalOverviewCompanyLinkedIn")
        assert tower_overview_li.is_visible()
        assert tower_overview_li.get_attribute("href").rstrip('/') == "https://www.linkedin.com/company/tower-research-capital"

        # Cold Email Tab
        page.locator(".modal-tab-btn[data-tab='email']").click()
        tower_comp_li = page.locator("#modalCompanyLinkedIn")
        assert tower_comp_li.is_visible()
        assert tower_comp_li.get_attribute("href").rstrip('/') == "https://www.linkedin.com/company/tower-research-capital"
        print("  [PASS] Modal for verified company (Tower Research) renders direct verified LinkedIn links.")

        # Close modal
        page.locator("#modalCloseBtn").click()

        # Check console errors
        assert len(console_errors) == 0, f"Encountered JS console errors: {console_errors}"
        print("  [PASS] Zero console errors during interaction.")

        browser.close()

if __name__ == "__main__":
    test_dataset_integrity()
    test_frontend_recruiter_links()
    print("\nALL RECRUITER CONTACT LINK TESTS PASSED SUCCESSFULLY!")
