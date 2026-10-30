"""dashboard_test.py - Verify existing dashboard features still work via HTTP."""
import urllib.request, sys

BASE = "http://127.0.0.1:5000"
PASS = 0
FAIL = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {name}")
        PASS += 1
    else:
        print(f"  [FAIL] {name}: {detail}")
        FAIL += 1

print("\n=== Dashboard Integrity Tests ===\n")

# 1. History Excel export
print("-- 1. History Excel export --")
r = urllib.request.urlopen(BASE + "/api/history/export", timeout=10)
content = r.read()
ct = r.headers.get("Content-Type", "")
test("Export returns data", len(content) > 1000, f"size={len(content)}")
test("Content-Type is xlsx", "spreadsheetml" in ct or "excel" in ct, ct)

# 2. Dashboard HTML structure
print("\n-- 2. Dashboard HTML structure --")
r2 = urllib.request.urlopen(BASE + "/index.html", timeout=10)
html = r2.read().decode("utf-8", errors="replace")
test("app.js tag present",         'src="app.js'         in html)
test("apply_auto.js tag present",  'src="apply_auto.js'  in html)
test("jobs_data.js tag present",   'src="jobs_data.js'   in html)
test("Detail modal present",       "detailModal"          in html)
test("KPI stat elements present",  "statTotalJobs"        in html)
test("Tier filter pills present",  "tierFilterPills"      in html)
test("Excel export button present","btnExcelMain"         in html)
test("Search input present",       "searchInput"          in html)
test("Status filter present",      "statusFilter"         in html)
test("Add company modal present",  "addCompanyModal"      in html)
test("Toast container present",    "toastContainer"       in html)

# 3. Static assets served
print("\n-- 3. Static assets --")
for asset in ["styles.css", "app.js", "apply_auto.js", "jobs_data.js", "test_form.html"]:
    try:
        r3 = urllib.request.urlopen(BASE + "/" + asset, timeout=5)
        body = r3.read()
        test(f"{asset} served ({len(body)} bytes)", len(body) > 100)
    except Exception as e:
        test(f"{asset} served", False, str(e))

# 4. CSS has auto-apply styles
print("\n-- 4. CSS auto-apply styles --")
r4 = urllib.request.urlopen(BASE + "/styles.css", timeout=5)
css = r4.read().decode("utf-8", errors="replace")
test("btn-auto-apply class present",   ".btn-auto-apply"   in css)
test("auto-apply-panel class present", ".auto-apply-panel" in css)
test("aap-confirm-section present",    ".aap-confirm-section" in css)
test("Original design vars preserved", "--bg-primary"      in css)
test("Gradient brand var preserved",   "--gradient-brand"  in css)

print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
sys.exit(0 if FAIL == 0 else 1)

