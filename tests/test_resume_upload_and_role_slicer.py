import os
import time
from playwright.sync_api import sync_playwright

def test_resume_upload_and_slicer():
    print("Running Playwright test for Resume Upload & Role Slicer...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto("http://127.0.0.1:5000", wait_until="networkidle")

        # 1. Verify header upload resume button
        btn_header_upload = page.locator("#btnHeaderUploadResume")
        assert btn_header_upload.is_visible(), "Header upload resume button must be visible"

        # 2. Verify resume hub card
        hub_card = page.locator("#resumeHubCard")
        assert hub_card.is_visible(), "Resume Hub card must be visible"
        hub_inactive = page.locator("#resumeHubInactive")
        assert hub_inactive.is_visible(), "Resume Hub inactive state must be visible initially"

        # 3. Verify Role Slicer section and counts
        role_slicer = page.locator("#roleSlicerPills")
        assert role_slicer.is_visible(), "Role Slicer pills container must be visible"
        
        all_roles_pill = page.locator('button.role-pill[data-role="all"]')
        ai_pill = page.locator('button.role-pill[data-role="ai-genai"]')
        ml_pill = page.locator('button.role-pill[data-role="ml"]')
        ds_pill = page.locator('button.role-pill[data-role="ds"]')
        de_pill = page.locator('button.role-pill[data-role="de"]')
        backend_pill = page.locator('button.role-pill[data-role="backend"]')
        intern_pill = page.locator('button.role-pill[data-role="intern"]')

        assert all_roles_pill.is_visible()
        assert ai_pill.is_visible()
        assert ml_pill.is_visible()
        assert ds_pill.is_visible()
        assert de_pill.is_visible()
        assert backend_pill.is_visible()
        assert intern_pill.is_visible()

        count_all = page.locator("#slicerCountAll").inner_text()
        print(f"Role Slicer All Roles count: {count_all}")
        assert int(count_all) >= 150, f"Expected >= 150 roles, got {count_all}"

        # 4. Test "⚡ Use Nitin's Resume" quick action
        btn_load_default = page.locator("#btnLoadDefaultResume")
        assert btn_load_default.is_visible()
        btn_load_default.click()

        # Wait for active state
        page.wait_for_selector("#resumeHubActive", state="visible")
        active_name = page.locator("#activeResumeName").inner_text()
        active_meta = page.locator("#activeResumeMeta").inner_text()
        print(f"Active Resume: {active_name} | Meta: {active_meta}")
        assert "Nitin_resume.pdf" in active_name or "resume" in active_name.lower()

        # Verify skills cloud rendered
        skills = page.locator("#activeResumeSkillsList .skill-chip")
        assert skills.count() >= 10, f"Expected >= 10 extracted skill chips, got {skills.count()}"

        # Verify sorting switched to highest fit first (fit-desc)
        sort_val = page.locator("#sortSelect").input_value()
        assert sort_val == "fit-desc", f"Expected sort 'fit-desc', got {sort_val}"

        # Verify first row has highest match score (95% - 98%)
        first_row_score = page.locator("#jobsTableBody tr:first-child .col-score .fit-badge").inner_text()
        print(f"First row match score: {first_row_score}")
        score_num = int(first_row_score.replace("%", "").strip())
        assert score_num >= 90, f"Expected top match >= 90%, got {score_num}"

        # Verify matched skills tag is present in table row
        matched_tag = page.locator("#jobsTableBody tr:first-child .matched-skills-tag")
        assert matched_tag.is_visible(), "Matched skills tag should be visible on top match row"
        print(f"First row matched skills text: {matched_tag.inner_text().encode('ascii', errors='replace').decode('ascii')}")

        # 5. Test Role Slicer: Click 'AI & GenAI'
        ai_pill.click()
        page.wait_for_timeout(300)
        assert "active" in ai_pill.get_attribute("class")
        assert "active" not in all_roles_pill.get_attribute("class")

        ai_rows_count = page.locator("#jobsTableBody tr").count()
        print(f"Filtered AI & GenAI rows count: {ai_rows_count}")
        assert ai_rows_count > 0 and ai_rows_count < int(count_all)
        
        # Verify top AI role still has high match
        top_ai_score = int(page.locator("#jobsTableBody tr:first-child .col-score .fit-badge").inner_text().replace("%", ""))
        assert top_ai_score >= 90, f"Expected top AI match >= 90%, got {top_ai_score}"

        # 6. Test Role Slicer: Click 'Data Engineer'
        de_pill.click()
        page.wait_for_timeout(300)
        de_rows_count = page.locator("#jobsTableBody tr").count()
        print(f"Filtered Data Engineer rows count: {de_rows_count}")
        assert de_rows_count > 0

        # 7. Test Reset back to All Roles
        all_roles_pill.click()
        page.wait_for_timeout(300)
        reset_rows_count = page.locator("#jobsTableBody tr").count()
        assert reset_rows_count == int(count_all), f"Expected reset to {count_all}, got {reset_rows_count}"

        # 8. Test Search Box with Role Slicer
        search_input = page.locator("#searchInput")
        search_input.fill("Discover")
        page.wait_for_timeout(300)
        searched_count = page.locator("#jobsTableBody tr").count()
        print(f"Rows after searching 'Discover': {searched_count}")
        assert searched_count >= 1

        # Clear search
        page.locator("#searchClear").click()
        page.wait_for_timeout(300)

        # 9. Test file input upload directly
        page.set_input_files("#resumeFileInput", "Nitin_resume.pdf")
        page.wait_for_selector("#resumeHubActive", state="visible")
        page.wait_for_timeout(800)
        assert "Nitin_resume.pdf" in page.locator("#activeResumeName").inner_text()
        print("Direct file upload via input tested successfully!")

        # 10. Test Reset Order button
        btn_reset_order = page.locator("#btnResetResumeOrder")
        btn_reset_order.click()
        page.wait_for_timeout(500)
        assert page.locator("#resumeHubInactive").is_visible(), "Inactive hub should be restored"
        assert page.locator("#sortSelect").input_value() == "date-desc"

        # Check console errors
        assert len(console_errors) == 0, f"Console errors found: {console_errors}"

        browser.close()
        print("\nALL RESUME UPLOAD AND ROLE SLICER TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_resume_upload_and_slicer()
