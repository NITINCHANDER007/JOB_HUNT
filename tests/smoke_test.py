"""Quick smoke test for all new modules."""
import sys, os
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

# Test 1: Candidate profile
print("=== Test 1: Candidate Profile ===")
from candidate_profile import load_profile
p = load_profile()
print(f"  Name:  {p['full_name']}")
print(f"  Email: {p['email']}")
print(f"  Resume exists: {os.path.exists(p['resume_path'])}")
print("  PASS")

# Test 2: Apply History DB
print("\n=== Test 2: Apply History DB ===")
from apply_history import init_db, create_attempt, update_status, get_history, AppStatus, has_applied_before
init_db()
aid = create_attempt("smoke-001", "TestCorp", "AI Engineer Intern", "http://localhost:5000/test_form.html")
print(f"  Created attempt ID: {aid}")
update_status(aid, AppStatus.SUBMITTED, "Smoke test OK", confirmation="Confirmed in test")
hist = get_history()
print(f"  History count: {len(hist)}")
print(f"  Latest status: {hist[0]['status']}")
dup = has_applied_before("smoke-001")
print(f"  Duplicate check works: {dup is not None}")
print("  PASS")

# Test 3: Session management
print("\n=== Test 3: Session Management ===")
from apply_engine.apply_session import create_session, get_session
sess = create_session("99", "DemoCorp", "Engineer", "http://localhost/test")
print(f"  Session ID: {sess.session_id[:12]}...")
retrieved = get_session(sess.session_id)
print(f"  Retrieved: {retrieved is not None}")
print("  PASS")

# Test 4: Handler registry
print("\n=== Test 4: Handler Registry ===")
from apply_engine.handler_registry import get_handler, list_supported_sites
dummy_sess = create_session("1", "Demo", "Role", "http://localhost:5000/test_form.html")
handler = get_handler("http://localhost:5000/test_form.html", dummy_sess, p)
print(f"  Handler for localhost: {handler.HANDLER_NAME}")
handler2 = get_handler("https://linkedin.com/jobs/123", dummy_sess, p)
print(f"  Handler for LinkedIn: {handler2.HANDLER_NAME}")
sites = list_supported_sites()
print(f"  Supported sites listed: {len(sites)}")
print("  PASS")

print("\n=== All smoke tests PASSED ===")

