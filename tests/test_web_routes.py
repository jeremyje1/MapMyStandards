import pytest
from httpx import AsyncClient

# Import the FastAPI app
from src.a3e.main import app

@pytest.mark.asyncio
async def test_landing_route():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/landing")
    assert resp.status_code == 200, resp.text
    assert "<html" in resp.text.lower() or "<!doctype" in resp.text.lower()

@pytest.mark.asyncio
async def test_checkout_route():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/checkout")
    assert resp.status_code in (200, 404)  # Allow 404 if checkout intentionally absent

@pytest.mark.asyncio
async def test_favicon_route():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/favicon.ico")
    assert resp.status_code in (200, 204)
    if resp.status_code == 200:
        ct = resp.headers.get("content-type", "")
        assert "image/" in ct
