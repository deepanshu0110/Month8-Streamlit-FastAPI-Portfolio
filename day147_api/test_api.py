import requests
import json

BASE = "http://127.0.0.1:8000"

def pretty(label, resp):
    print(f"\n{'─'*60}")
    print(f"  {label}  [Status {resp.status_code}]")
    print(json.dumps(resp.json(), indent=2))

# 1. GET /
r = requests.get(f"{BASE}/")
pretty("GET /", r)

# 2. GET /model-info
r = requests.get(f"{BASE}/model-info")
pretty("GET /model-info", r)

# 3. POST /predict
payload = {
    "hourly_rate": 25.0,
    "client_rating": 4.2,
    "bids_received": 18.0,
    "duration_days": 45.0,
    "milestones": 4,
    "revision_rounds": 2,
    "category": "Data Science",
    "experience_level": "Mid",
    "payment_type": "Fixed"
}
r = requests.post(f"{BASE}/predict", json=payload)
pretty("POST /predict (single)", r)

# 4. POST /predict-batch
batch_payload = {
    "projects": [
        payload,
        {
            "hourly_rate": 5.0,
            "client_rating": 1.5,
            "bids_received": 55.0,
            "duration_days": 110.0,
            "milestones": 1,
            "revision_rounds": 4,
            "category": "Content Writing",
            "experience_level": "Junior",
            "payment_type": "Hourly"
        }
    ]
}
r = requests.post(f"{BASE}/predict-batch", json=batch_payload)
pretty("POST /predict-batch (2 projects)", r)

# 5. Validation error
bad_payload = dict(payload)
bad_payload["category"] = "Invalid"
r = requests.post(f"{BASE}/predict", json=bad_payload)
pretty("POST /predict (bad category → 422)", r)

print("\n✅ All tests done.")