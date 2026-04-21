import os

os.environ.setdefault("database_url", "postgresql://test:test@localhost/test")
os.environ.setdefault("openai_api_key", "sk-test")

from fastapi.testclient import TestClient

from app.main import app
from app.models import QueryResponse
from app.routers import query as query_router


class _FakeProcessor:
    async def process_query(self, query: str, student_id, correlation_id: str | None = None):
        return QueryResponse(
            answer=f"Answer for: {query}",
            confidence=0.88,
            correlation_id=correlation_id,
            sources=[],
        )


def test_query_route_supports_gateway_path(monkeypatch):
    monkeypatch.setattr(query_router, "get_query_processor", lambda: _FakeProcessor())
    client = TestClient(app)

    response = client.post(
        "/query",
        json={
            "student_id": "11111111-1111-1111-1111-111111111111",
            "query": "What is due this week?",
            "type": "text",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Answer for: What is due this week?"
    assert body["confidence"] == 0.88


def test_query_route_keeps_legacy_process_path(monkeypatch):
    monkeypatch.setattr(query_router, "get_query_processor", lambda: _FakeProcessor())
    client = TestClient(app)

    response = client.post(
        "/api/query/process",
        json={
            "student_id": "11111111-1111-1111-1111-111111111111",
            "query": "Summarize my announcements",
            "type": "text",
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Answer for: Summarize my announcements"
