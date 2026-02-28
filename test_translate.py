import requests
import json

base_url = "http://localhost:8001"

# 1. Login or Register
email = "test_translate@example.com"
password = "password123"

# register first (ignore if exists)
requests.post(f"{base_url}/auth/register", json={"email": email, "password": password, "name": "Test User"})

# login
resp = requests.post(f"{base_url}/auth/login", json={"email": email, "password": password})
token = resp.json().get("token")

# 2. Translate
headers = {"Authorization": f"Bearer {token}"}
payload = {"text": "hello", "source_lang": "en", "target_lang": "te"}

resp = requests.post(f"{base_url}/translate", json=payload, headers=headers)
print("Translate Response:", resp.json())
