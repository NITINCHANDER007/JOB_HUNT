"""run_tests.py
Master test runner for the Job Hunt Intelligence project.
Executes all automated test suites located in the tests/ directory.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
TESTS_DIR = ROOT_DIR / "tests"

TEST_SUITES = [
    ("Dashboard Integrity", "dashboard_test.py"),
    ("Core Smoke Tests", "smoke_test.py"),
    ("Auto-Apply API Suite", "api_test.py"),
    ("Company & Recruiter Links", "test_company_and_recruiter_links.py"),
    ("Recruiter Link Audit", "test_recruiter_links.py"),
    ("Contact Link Interactions", "test_contact_clicks.py"),
    ("Live Refresh & Authentic Dates", "test_refresh_live_jobs.py"),
    ("Excel Download Format", "test_excel_export_format.py"),
    ("Resume Upload & Role Slicer", "test_resume_upload_and_role_slicer.py"),
    ("Autonomous Features Suite", "test_autonomous_features.py"),
    ("Complete Auto-Apply Suite", "test_auto_apply_complete.py")
]

def main():
    print("=" * 70)
    print("   JOB HUNT INTELLIGENCE — MASTER TEST SUITE RUNNER")
    print("=" * 70)
    
    total_suites = len(TEST_SUITES)
    passed_suites = 0
    failed_suites = 0
    results = []

    start_total = time.time()

    for name, script_name in TEST_SUITES:
        script_path = TESTS_DIR / script_name
        if not script_path.exists():
            print(f"\n[SKIP] {name} ({script_name} not found in tests/)")
            results.append((name, "SKIPPED", 0))
            continue

        print(f"\n>>> Running: {name} ({script_name})...")
        t0 = time.time()
        res = subprocess.run([sys.executable, str(script_path)], cwd=str(ROOT_DIR))
        elapsed = time.time() - t0

        if res.returncode == 0:
            print(f"  --> [PASS] {name} in {elapsed:.2f}s")
            passed_suites += 1
            results.append((name, "PASSED", elapsed))
        else:
            print(f"  --> [FAIL] {name} in {elapsed:.2f}s (exit code {res.returncode})")
            failed_suites += 1
            results.append((name, "FAILED", elapsed))

    total_time = time.time() - start_total

    print("\n" + "=" * 70)
    print("                       SUMMARY OF RESULTS")
    print("=" * 70)
    for name, status, elapsed in results:
        status_colored = f"[{status}]"
        print(f"  {status_colored:10} {name:35} ({elapsed:.2f}s)")
    
    print("-" * 70)
    print(f"  Total Suites: {total_suites} | Passed: {passed_suites} | Failed: {failed_suites} | Time: {total_time:.2f}s")
    print("=" * 70)

    sys.exit(0 if failed_suites == 0 else 1)

if __name__ == "__main__":
    main()

