"""
test_contact_clicks.py
Automated acceptance tests for Contact Details Click Functionality.
Runs headless browser checks against the running dashboard.
"""

import asyncio
import sys
import os

# UTF-8 console output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:5000/index.html"

async def run_tests():
    console_errors = []
    pass_count = 0
    fail_count = 0

    def record(name, condition, extra=""):
        nonlocal pass_count, fail_count
        if condition:
            print(f"[PASS] {name}")
            pass_count += 1
        else:
            print(f"[FAIL] {name}: {extra}")
            fail_count += 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Capture console messages
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        print("Navigating to dashboard...")
        await page.goto(BASE_URL, wait_until="networkidle")

        # 1. Console errors check
        record("Zero JavaScript console errors on initial load", len(console_errors) == 0, str(console_errors))

        # 2. Table View: CredHive row is clean without bloated badges
        print("\n--- Testing Table View Clean Rendering ---")
        credhive_row = page.locator("#jobsTableBody tr:has-text('CredHive')")
        record("CredHive row rendered", await credhive_row.count() > 0)

        col_comp = credhive_row.locator(".col-company")
        badges_count = await col_comp.locator(".contact-badge, .source-badge").count()
        record("CredHive table company cell is clean without bloated badges", badges_count == 0)

        # 3. Card View: CredHive contacts
        print("\n--- Testing Card View Contacts ---")
        await page.click("#viewGridBtn")
        await asyncio.sleep(0.5)

        credhive_card = page.locator("#cardsViewSection .job-card:has-text('CredHive')")
        record("CredHive card rendered in Card View", await credhive_card.count() > 0)

        card_email = credhive_card.locator("a.contact-email-badge")
        record("CredHive card email link exists", await card_email.count() > 0)
        if await card_email.count() > 0:
            href = await card_email.get_attribute("href")
            record("CredHive card email mailto is correct", href == "mailto:maghav@credhive.in", href)

        card_company = credhive_card.locator("a.contact-company-badge")
        record("CredHive card Company LinkedIn link exists", await card_company.count() > 0)
        if await card_company.count() > 0:
            href = await card_company.get_attribute("href")
            record("CredHive card Company LinkedIn URL is correct", "linkedin.com/company/credhive-fintech" in href, href)

        card_recruiter = credhive_card.locator("a.contact-recruiter-search-badge")
        record("CredHive card Recruiter search link exists", await card_recruiter.count() > 0)
        if await card_recruiter.count() > 0:
            href = await card_recruiter.get_attribute("href")
            record("CredHive card Recruiter People search URL is correct", "linkedin.com/search/results/people/?keywords=" in href and "Maghav%20Kumar" in href, href)

        # 4. Modal View: Overview & Cold Email Tabs
        print("\n--- Testing Modal Contacts ---")
        # Open modal from CredHive card
        modal_btn = credhive_card.locator(".btn-open-modal")
        await modal_btn.click()
        await page.wait_for_selector("#detailModal.show", timeout=3000)

        # Check Overview Tab contacts
        ov_card = page.locator("#modalOverviewContactCard")
        record("Modal Overview recruiter contact card visible", await ov_card.is_visible())

        ov_email = page.locator("#modalOverviewEmail")
        record("Modal Overview email link visible", await ov_email.is_visible())
        if await ov_email.is_visible():
            href = await ov_email.get_attribute("href")
            record("Modal Overview email href is mailto:maghav@credhive.in", href == "mailto:maghav@credhive.in", href)

        ov_company = page.locator("#modalOverviewCompanyLinkedIn")
        record("Modal Overview Company LinkedIn link visible", await ov_company.is_visible())
        if await ov_company.is_visible():
            href = await ov_company.get_attribute("href")
            target = await ov_company.get_attribute("target")
            record("Modal Overview Company LinkedIn href is correct", "linkedin.com/company/credhive-fintech" in href, href)
            record("Modal Overview Company LinkedIn target is _blank", target == "_blank", target)

        ov_recruiter = page.locator("#modalOverviewRecruiterLinkedIn")
        record("Modal Overview Recruiter LinkedIn link visible", await ov_recruiter.is_visible())
        if await ov_recruiter.is_visible():
            href = await ov_recruiter.get_attribute("href")
            record("Modal Overview Recruiter LinkedIn search href is correct", "linkedin.com/search/results/people/?keywords=" in href and "Maghav%20Kumar" in href, href)

        # Switch to Cold Email Tab
        await page.click(".modal-tab-btn[data-tab='email']")
        await asyncio.sleep(0.3)

        ce_email = page.locator("#modalContactEmail")
        record("Cold Email tab email link visible", await ce_email.is_visible())
        if await ce_email.is_visible():
            href = await ce_email.get_attribute("href")
            record("Cold Email tab email is mailto:maghav@credhive.in", href == "mailto:maghav@credhive.in", href)

        ce_company = page.locator("#modalCompanyLinkedIn")
        record("Cold Email tab Company LinkedIn button visible", await ce_company.is_visible())
        if await ce_company.is_visible():
            href = await ce_company.get_attribute("href")
            record("Cold Email tab Company LinkedIn href is correct", "linkedin.com/company/credhive-fintech" in href, href)

        ce_recruiter = page.locator("#modalRecruiterLinkedIn")
        record("Cold Email tab Recruiter LinkedIn button visible", await ce_recruiter.is_visible())
        if await ce_recruiter.is_visible():
            href = await ce_recruiter.get_attribute("href")
            target = await ce_recruiter.get_attribute("target")
            record("Cold Email tab Recruiter LinkedIn People search href is correct", "linkedin.com/search/results/people/?keywords=" in href and "Maghav%20Kumar" in href, href)
            record("Cold Email tab Recruiter LinkedIn target is _blank", target == "_blank", target)
            record("Cold Email tab LinkedIn target is _blank", target == "_blank", target)

        # Close modal
        await page.click("#modalCloseBtn")
        await asyncio.sleep(0.3)

        # 5. Non-interference check
        print("\n--- Testing Non-interference & Other Features ---")
        await page.click("#viewTableBtn")
        await asyncio.sleep(0.3)

        # Check filter still works
        await page.fill("#searchInput", "CredHive")
        await asyncio.sleep(0.3)
        rows_after_search = await page.locator("#jobsTableBody tr").count()
        record("Search filter works after contact click fix", rows_after_search >= 1, f"rows: {rows_after_search}")

        await page.click("#searchClear")
        await asyncio.sleep(0.3)
        rows_after_clear = await page.locator("#jobsTableBody tr").count()
        record("Search clear resets list", rows_after_clear > 1, f"rows: {rows_after_clear}")

        # Check export dropdown still opens
        await page.click("#btnExcelMain")
        dropdown_show = await page.locator("#exportDropdown.show").count()
        record("Excel export dropdown opens", dropdown_show == 1)
        await page.click("body")  # close dropdown

        # Final console error check
        record("Zero JS errors during all interactions", len(console_errors) == 0, str(console_errors))

        await browser.close()

    print(f"\n==========================================")
    print(f"Test Summary: {pass_count} passed, {fail_count} failed")
    print(f"==========================================")
    return fail_count == 0

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)

