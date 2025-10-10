from fastapi.testclient import TestClient

from src.a3e.main import app

client = TestClient(app)


def test_feature_flags_endpoint_returns_flags():
    response = client.get("/api/v1/feature-flags")
    assert response.status_code == 200
    data = response.json()
    assert "standards_graph" in data


def test_standards_graph_stub():
    response = client.get("/api/v1/intelligence/standards-graph")
    assert response.status_code == 200
    payload = response.json()
    assert "graph" in payload
    assert payload["graph"]["nodes"]


def test_evidence_mapper_stub():
    response = client.get("/api/v1/intelligence/evidence-mapper")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mappings"][0]["evidence_id"]


def test_evidence_trust_stub():
    response = client.get("/api/v1/intelligence/evidence-trust")
    assert response.status_code == 200
    payload = response.json()
    assert payload["documents"][0]["trust_score"]


def test_gap_risk_stub():
    response = client.get("/api/v1/intelligence/gap-risk")
    assert response.status_code == 200
    payload = response.json()
    assert "risk_profile" in payload


def test_crosswalk_stub():
    response = client.get("/api/v1/intelligence/crosswalkx")
    assert response.status_code == 200
    payload = response.json()
    assert payload["matches"]


def test_citeguard_stub():
    response = client.get("/api/v1/intelligence/citeguard")
    assert response.status_code == 200
    payload = response.json()
    assert payload["issues"]
