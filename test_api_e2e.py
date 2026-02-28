"""Quick E2E API test for all booking intents."""
import requests, time, sys

API = "http://localhost:8001"

# Auth
try:
    r = requests.post(f"{API}/auth/register", json={"email":"final@t.com","password":"p","name":"F"}, timeout=10)
    if r.status_code != 200:
        r = requests.post(f"{API}/auth/login", json={"email":"final@t.com","password":"p"}, timeout=10)
    token = r.json()["token"]
except Exception as e:
    print(f"Auth failed: {e}")
    sys.exit(1)

h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("Token OK\n")

tests = [
    ("I want a bus ticket to vijayawada", "bus_booking"),
    ("book a cab to the airport", "taxi_booking"),
    ("find flights to delhi", "flight_booking"),
    ("find a hotel in goa", "hotel_booking"),
]

ok = 0
for text, expected in tests:
    t0 = time.time()
    try:
        r = requests.post(f"{API}/agent/process", json={"text": text}, headers=h, timeout=30)
        ms = int((time.time() - t0) * 1000)
        data = r.json()
        intent = data.get("intent", "?")
        auto = data.get("automation_triggered", False)
        resp = data.get("response", "")[:60]
        passed = intent == expected
        if passed:
            ok += 1
        tag = "PASS" if passed else "FAIL"
        print(f"  {tag} | {text}")
        print(f"       -> intent={intent} auto={auto} [{ms}ms]")
        print(f"       -> response: {resp}")
    except Exception as e:
        print(f"  FAIL | {text} -> ERROR: {e}")
    print()

print(f"Results: {ok}/{len(tests)} passed")
