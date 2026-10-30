"""
live_test_demo.py
Live Playwright test against the local test_form.html.
Run this AFTER starting auto_apply_server.py in a separate terminal.

Tests:
  1. Open test_form.html
  2. Fill all form fields using candidate profile
  3. Upload resume
  4. Verify fields are filled
  5. Submit (demo form only - not a real employer)
  6. Verify success message
"""
import asyncio
import sys
import os

# Fix Windows console encoding for Unicode output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

from candidate_profile import load_profile
from playwright.async_api import async_playwright

TEST_URL = "http://localhost:5000/test_form.html"


async def run_test():
    profile = load_profile()
    print(f"Profile loaded: {profile['full_name']}")
    print(f"Resume: {profile['resume_path']}")
    print(f"\nOpening test form at: {TEST_URL}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()

        print("Navigating to test form...")
        await page.goto(TEST_URL, wait_until="domcontentloaded")
        await asyncio.sleep(1)

        # Check form exists
        form = await page.query_selector("form#demo-apply-form")
        assert form is not None, "FAIL: Demo form not found on page"
        print("[PASS] Form detected")

        # Fill fields
        await page.fill('input[name="full_name"]', profile["full_name"])
        await page.fill('input[name="email"]', profile["email"])
        await page.fill('input[name="phone"]', profile["phone"])
        await page.fill('input[name="linkedin"]', profile["linkedin"])
        await page.fill('input[name="college"]', profile["college"])
        await page.fill('input[name="degree"]', profile["degree"])
        await page.fill('input[name="graduation_year"]', profile["graduation_year"])
        await page.fill('input[name="cgpa"]', profile["cgpa"])
        skills_text = ", ".join(profile.get("skills", [])[:8])
        await page.fill('textarea[name="skills"]', skills_text)
        await page.fill('input[name="role_interest"]', "AI Engineer Intern")
        print("[PASS] All text fields filled")

        # Upload resume
        resume_input = await page.query_selector('input[type="file"]')
        if resume_input:
            await resume_input.set_input_files(profile["resume_path"])
            print("[PASS] Resume uploaded")
        else:
            print("[WARN] Resume input not found (test still continues)")

        # Verify a field value
        filled_name = await page.input_value('input[name="full_name"]')
        assert filled_name == profile["full_name"], f"FAIL: name mismatch: {filled_name!r}"
        print(f"[PASS] Verification: full_name = {filled_name!r}")

        filled_email = await page.input_value('input[name="email"]')
        assert filled_email == profile["email"], f"FAIL: email mismatch"
        print(f"[PASS] Verification: email = {filled_email!r}")

        print("\n[...] Pausing 3 seconds for visual review...")
        await asyncio.sleep(3)

        # Submit the demo form
        print("Submitting demo form...")
        await page.click('button[type="submit"]')
        await asyncio.sleep(1)

        # Verify success message
        success = await page.query_selector("#submission-success")
        success_visible = await success.is_visible() if success else False
        assert success_visible, "FAIL: Success message not shown after submit"
        print("[PASS] Success message displayed after submission")

        print("\n=== ALL LIVE TESTS PASSED ===")
        await asyncio.sleep(2)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_test())

