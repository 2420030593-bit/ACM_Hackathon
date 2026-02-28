import requests
import json
import time

base_url = "http://localhost:8001"

# 1. Login to get token
resp = requests.post(f"{base_url}/auth/login", json={"email": "test_translate@example.com", "password": "password123"})
if resp.status_code != 200:
    print("Login failed")
    exit(1)
token = resp.json().get("token")
headers = {"Authorization": f"Bearer {token}"}

# 2. Test the agent/process endpoint with a custom/arbitrary request
# We are intentionally picking something NOT in the hardcoded handler list
payload = {"text": "book me movie tickets for Inception tonight"}
print(f"Sending request: {payload['text']}")
resp = requests.post(f"{base_url}/agent/process", json=payload, headers=headers)

if resp.status_code == 200:
    data = resp.json()
    print("Intent:", data.get("intent"))
    print("Automation Triggered:", data.get("automation_triggered"))
    print("Response:", data.get("response"))
    
    # 3. Simulate frontend automatically triggering automation endpoint
    if data.get("automation_triggered"):
        print("\nFiring /automation/execute endpoint...")
        details = data.get("bookings")[0].get("details", {}) if data.get("bookings") else {}
        auto_payload = {
            "intent": data.get("intent"),
            "destination": "movie tickets",
            "details": details
        }
        resp = requests.post(f"{base_url}/automation/execute", json=auto_payload)
        print("Automation API Response:", resp.json())
        print("Waiting 30 seconds for browser visualization...")
        time.sleep(30)
else:
    print("Error:", resp.text)
