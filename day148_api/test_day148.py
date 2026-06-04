import httpx
import json

BASE = "http://127.0.0.1:8000"
ADMIN_KEY = "freelancehub-2024-secret"
READONLY_KEY = "client-readonly-key-001"

def pretty(label, resp):
    print(f"\n{'─'*60}")
    print(f"  {label}  [Status {resp.status_code}]")
    try:
        print(json.dumps(resp.json(), indent=2))
    except:
        print(resp.text)

def test():
    # 1. GET / – no auth required
    r = httpx.get(f"{BASE}/")
    pretty("GET /", r)
    assert r.status_code == 200

    # 2. POST /seed-db with admin key
    headers = {"X-API-Key": ADMIN_KEY}
    r = httpx.post(f"{BASE}/seed-db", headers=headers)
    pretty("POST /seed-db", r)
    assert r.status_code == 200
    assert r.json()["seeded"] == 500

    # 3. GET /projects/stats
    r = httpx.get(f"{BASE}/projects/stats", headers=headers)
    pretty("GET /projects/stats", r)
    assert r.status_code == 200
    data = r.json()
    assert data["total_projects"] == 500
    assert data["completed"] == 269   # from fixed seed

    # 4. GET /projects/filter?status=Cancelled
    r = httpx.get(f"{BASE}/projects/filter?status=Cancelled", headers=headers)
    pretty("GET /projects/filter?status=Cancelled", r)
    assert r.status_code == 200
    assert r.json()["count"] == 141

    # 5. GET /projects with invalid key → 401
    bad_headers = {"X-API-Key": "wrong-key"}
    r = httpx.get(f"{BASE}/projects", headers=bad_headers)
    pretty("GET /projects (invalid key)", r)
    assert r.status_code == 401

    # 6. POST /predict (no auth needed) – background task test
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
    r = httpx.post(f"{BASE}/predict", json=payload)
    pretty("POST /predict", r)
    assert r.status_code == 200
    assert "prediction" in r.json()

    # ★ Bonus: test DELETE with readonly key → 403
    r = httpx.delete(f"{BASE}/projects/1", headers={"X-API-Key": READONLY_KEY})
    pretty("DELETE /projects/1 (readonly key)", r)
    assert r.status_code == 403

    print("\n✅ All tests passed.")

if __name__ == "__main__":
    test()