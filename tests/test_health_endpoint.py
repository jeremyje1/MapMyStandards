import pytest
from httpx import AsyncClient, ASGITransport
from src.a3e.main import app

@pytest.mark.asyncio
async def test_health_endpoint_basic():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/health")
    assert resp.status_code in (200, 503)
    data = resp.json()
    # Required top-level keys
    for key in ("status", "timestamp", "services", "capabilities"):
        assert key in data
    assert "database" in data["services"]
    # Database must report status
    assert "status" in data["services"]["database"]
    # If degraded, still 200
    if data["status"] == "degraded":
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_health_endpoint_optional_flags():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/health")
    data = resp.json()
    # Capabilities booleans present
    caps = data.get("capabilities", {})
    assert "proprietary_ontology" in caps and isinstance(caps["proprietary_ontology"], bool)
    assert "audit_traceability" in caps
