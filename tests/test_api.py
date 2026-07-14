from fastapi.testclient import TestClient

from nyxora_concierge.config import Settings
from nyxora_concierge.main import create_app


def test_health_endpoint(tmp_path) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "api.db")))
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.2.0"}


def test_chat_endpoint(tmp_path) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "api.db")))
    with TestClient(app) as client:
        response = client.post(
            "/v1/chat",
            json={
                "session_id": "web-session-123",
                "message": "I want to book a consultation next week",
                "consent_to_store": False,
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "booking"
    assert payload["recommended_action"] == "book_consultation"


def test_invalid_session_is_rejected(tmp_path) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "api.db")))
    with TestClient(app) as client:
        response = client.post(
            "/v1/chat",
            json={"session_id": "bad id", "message": "hello"},
        )
    assert response.status_code == 422
