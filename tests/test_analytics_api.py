import pytest
from httpx import AsyncClient, ASGITransport

from src.a3e.main import app
from src.a3e.api.dependencies import get_current_user, has_active_subscription


@pytest.fixture(autouse=True)
def override_dependencies():
    """Provide deterministic auth + subscription checks for analytics tests."""
    user_payload = {
        "id": "test-user",
        "user_id": "test-user",
        "email": "test@example.com",
        "plan": "professional",
        "subscription_status": "active",
    }
    app.dependency_overrides[get_current_user] = lambda: user_payload
    app.dependency_overrides[has_active_subscription] = lambda: user_payload
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dashboard_metrics_returns_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert set(payload["data"]).issuperset(
        {"compliance_score", "documents_analyzed", "time_saved"}
    )


@pytest.mark.asyncio
async def test_record_processed_document_mutates_metrics():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        post_payload = {
            "document_id": "doc-123",
            "standard_mappings": ["STD-1", "STD-2"],
            "metrics": {"compliance_score": 82.5},
            "analysis": {"potential_gaps": ["gap-1"]},
        }
        post_resp = await ac.post(
            "/api/v1/analytics/document/processed", json=post_payload
        )
        assert post_resp.status_code == 200
        assert post_resp.json()["success"] is True

        metrics_resp = await ac.get("/api/v1/analytics/dashboard/metrics")

    assert metrics_resp.status_code == 200
    metrics_payload = metrics_resp.json()["data"]
    assert metrics_payload["documents_analyzed"] >= 1
    assert metrics_payload["standards_mapped"] >= 2
    assert metrics_payload["gaps_identified"] >= 1


@pytest.mark.asyncio
async def test_realtime_metrics_requires_subscription_override():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/realtime/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert "metrics" in payload
    assert payload["next_update_in"] == 30
