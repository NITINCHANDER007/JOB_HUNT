"""
api_test.py
End-to-end API tests against the running FastAPI server.
Tests: profile, apply, status, duplicate prevention, history, supported-sites.
Server must be running at http://127.0.0.1:5000 before running this.
"""
import sys, json
import urllib.request, urllib.error

BASE = "http://127.0.0.1:5000"
PASS = 0
FAIL = 0

def req(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {name}")
        PASS += 1
    else:
        print(f"  [FAIL] {name}: {detail}")
        FAIL += 1

print("\n=== API Test Suite ===\n")

# 1. Health check
print("-- 1. Health check --")
status, data = req("GET", "/api/health")
test("Health endpoint returns 200", status == 200)
test("Status field is 'ok'", data.get("status") == "ok")

# 2. Profile endpoint
print("\n-- 2. Profile endpoint --")
status, data = req("GET", "/api/profile")
test("Profile returns 200", status == 200)
test("full_name is Nitin Chander", data.get("full_name") == "Nitin Chander")
test("email is present", bool(data.get("email")))
test("resume_path is present", bool(data.get("resume_path")))
test("No private _keys exposed", not any(k.startswith("_") for k in data))

# 3. Supported sites
print("\n-- 3. Supported sites --")
status, data = req("GET", "/api/supported-sites")
test("Supported sites returns 200", status == 200)
test("At least 2 sites listed", isinstance(data, list) and len(data) >= 2)

# 4. Start an application (test form)
print("\n-- 4. Start application session --")
status, data = req("POST", "/api/apply", {
    "job_id": "api-test-99",
    "company": "API Test Corp",
    "role": "Test Engineer",
    "apply_url": "http://localhost:5000/test_form.html",
    "force": True
})
test("Apply returns 200", status == 200)
test("session_id returned", bool(data.get("session_id")))
session_id = data.get("session_id", "")

# 5. Poll session status
if session_id:
    print("\n-- 5. Session status --")
    status, data = req("GET", f"/api/apply/{session_id}/status")
    test("Status returns 200", status == 200)
    test("session_id matches", data.get("session_id") == session_id)
    test("status field present", "status" in data)
    print(f"  (current status: {data.get('status')})")

# 6. Abort the session
if session_id:
    print("\n-- 6. Abort session --")
    status, data = req("POST", f"/api/apply/{session_id}/abort")
    test("Abort returns 200", status == 200)

# 7. Duplicate prevention
print("\n-- 7. Duplicate prevention --")
# The smoke_test.py already recorded job_id=smoke-001 as Submitted
status, data = req("POST", "/api/apply", {
    "job_id": "smoke-001",
    "company": "TestCorp",
    "role": "AI Engineer Intern",
    "apply_url": "http://localhost:5000/test_form.html",
    "force": False
})
test("Duplicate check fires", status == 200 and data.get("status") == "duplicate", str(data))

# force=True bypasses duplicate check
status, data = req("POST", "/api/apply", {
    "job_id": "smoke-001",
    "company": "TestCorp",
    "role": "AI Engineer Intern",
    "apply_url": "http://localhost:5000/test_form.html",
    "force": True
})
test("force=True creates new session", status == 200 and bool(data.get("session_id")), str(data))
force_sid = data.get("session_id", "")
if force_sid:
    req("POST", f"/api/apply/{force_sid}/abort")  # clean up

# 8. Bad URL validation
print("\n-- 8. Input validation --")
status, data = req("POST", "/api/apply", {
    "job_id": "bad-99",
    "company": "BadCo",
    "role": "Test",
    "apply_url": "not-a-url"
})
test("Bad URL rejected with 400", status == 400, str(data))

# 9. History endpoint
print("\n-- 9. Application history --")
status, data = req("GET", "/api/history")
test("History returns 200", status == 200)
test("History is a list", isinstance(data, list))
test("History has records", len(data) > 0, f"count={len(data)}")

print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
sys.exit(0 if FAIL == 0 else 1)

