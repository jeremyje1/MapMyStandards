import os
import json
from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.a3e.api.routes import user_intelligence_simple


app_for_tests = FastAPI()
app_for_tests.include_router(user_intelligence_simple.router)
client = TestClient(app_for_tests)


@pytest.fixture
def persisted_analysis_setup(monkeypatch):
    stored_summary = {
        "overall_score": 0.91,
        "details": {"benchmark": "A+"},
        "_marker": "persisted",
    }
    stored_payload = {
        "trust_summary": stored_summary,
        "trust_score": {"overall_score": 0.91},
    }

    now = datetime.utcnow()
    document_row = SimpleNamespace(
        id="doc-123",
        filename="demo.pdf",
        status="analyzed",
        uploaded_at=now,
        updated_at=now,
        file_size=2048,
        content_type="application/pdf",
        analysis_results=json.dumps(stored_payload),
        standards_mapped=1,
    )

    mapping_rows = [
        SimpleNamespace(
            standard_id="sacscoc.1.1",
            confidence=0.87,
            excerpts=json.dumps([{"page": 1, "snippet": "Example"}]),
        )
    ]

    class FakeResult:
        def __init__(self, rows):
            self._rows = rows

        def first(self):
            return self._rows[0] if self._rows else None

        def __iter__(self):
            return iter(self._rows)

    class FakeSession:
        async def execute(self, statement, params=None):
            sql = str(statement).lower()
            if "from documents" in sql:
                return FakeResult([document_row])
            if "from evidence_mappings" in sql:
                return FakeResult(mapping_rows)
            return FakeResult([])

        async def close(self):
            return None

    @asynccontextmanager
    async def fake_get_session():
        yield FakeSession()

    async def override_current_user():
        return {
            "email": "test@example.com",
            "user_id": "user-123",
            "sub": "user-123",
        }

    monkeypatch.setattr(user_intelligence_simple, "db_manager", SimpleNamespace(get_session=fake_get_session))
    app_for_tests.dependency_overrides[user_intelligence_simple.get_current_user_simple] = override_current_user

    yield stored_summary

    app_for_tests.dependency_overrides.pop(user_intelligence_simple.get_current_user_simple, None)


def test_stored_analysis_trust_summary_surfaces(persisted_analysis_setup):
    response = client.get("/api/user/intelligence-simple/documents/doc-123/analysis")

    assert response.status_code == 200
    payload = response.json()
    trust_summary = payload["analysis"]["trust_summary"]

    assert trust_summary["_marker"] == persisted_analysis_setup["_marker"]
    assert trust_summary == persisted_analysis_setup
