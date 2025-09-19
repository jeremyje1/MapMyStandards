import os
import jwt
import requests

BASE_URL = os.environ.get("MMS_API_BASE", "http://localhost:8000")
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "your-secret-key-here-change-in-production")


def _make_token():
    payload = {
        "email": "tester@example.com",
        "user_id": "tester-123",
        "primary_accreditor": "HLC",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def test_dashboard_metrics_bounds():
    token = _make_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/api/user/intelligence-simple/dashboard/overview"
    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code == 200
    data = resp.json().get("data") or {}
    perf = data.get("performance_metrics") or {}
    comp = float(perf.get("compliance_score") or 0)
    cov = float(perf.get("coverage_percentage") or 0)
    avg_trust = float(perf.get("average_trust") or 0)

    assert 0.0 <= comp <= 100.0
    assert 0.0 <= cov <= 100.0
    assert 0.0 <= avg_trust <= 1.0
