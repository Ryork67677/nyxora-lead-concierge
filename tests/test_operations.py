import hashlib
import sqlite3
from contextlib import closing

from fastapi.testclient import TestClient

from nyxora_concierge.config import Settings
from nyxora_concierge.main import create_app
from nyxora_concierge.repository import RepositoryError

METRICS_KEY = "metrics-test-key"
METRICS_KEY_HASH = hashlib.sha256(METRICS_KEY.encode()).hexdigest()


def test_readiness_checks_storage_and_knowledge_base(tmp_path) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "ready.db")))
    with TestClient(app) as client:
        response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "version": "0.3.0",
        "database": "ok",
        "knowledge_base": "ok",
    }


def test_readiness_returns_structured_503_when_database_fails(tmp_path, monkeypatch) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "failed-ready.db")))
    with TestClient(app) as client:
        monkeypatch.setattr(
            app.state.repository,
            "check",
            lambda: (_ for _ in ()).throw(RepositoryError("private database detail")),
        )
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.headers["retry-after"] == "30"
    assert response.json()["title"] == "Service temporarily unavailable"
    assert "private database detail" not in response.text


def test_readiness_fails_when_required_schema_is_missing(tmp_path) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "missing-schema.db")))
    with TestClient(app) as client:
        with closing(sqlite3.connect(app.state.repository.database_path)) as connection:
            connection.execute("DROP TABLE conversation_events")
            connection.commit()
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["title"] == "Service temporarily unavailable"


def test_storage_failure_returns_structured_503(tmp_path, monkeypatch) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "failed-write.db")))
    with TestClient(app) as client:
        monkeypatch.setattr(
            app.state.repository,
            "record",
            lambda *_: (_ for _ in ()).throw(RepositoryError("write detail")),
        )
        response = client.post(
            "/v1/chat",
            json={
                "session_id": "storage-failure-1",
                "message": "Book a consultation",
                "consent_to_store": True,
            },
        )

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "write detail" not in response.text


def test_metrics_are_authenticated_and_capture_bounded_outcomes(tmp_path) -> None:
    settings = Settings(
        app_env="production",
        database_path=str(tmp_path / "metrics.db"),
        api_key_hashes=(METRICS_KEY_HASH,),
    )
    app = create_app(settings)
    headers = {"Authorization": f"Bearer {METRICS_KEY}"}
    with TestClient(app) as client:
        assert client.get("/metrics").status_code == 401
        chat = client.post(
            "/v1/chat",
            headers=headers,
            json={"session_id": "metrics-session-1", "message": "Book a consultation"},
        )
        metrics = client.get("/metrics", headers=headers)

    assert chat.status_code == 200
    assert metrics.status_code == 200
    assert "nyxora_http_requests_total" in metrics.text
    assert "nyxora_http_request_duration_seconds" in metrics.text
    assert "nyxora_concierge_responses_total" in metrics.text
    assert 'intent="booking"' in metrics.text
    assert "metrics-session-1" not in metrics.text


def test_metrics_can_be_disabled(tmp_path) -> None:
    app = create_app(
        Settings(database_path=str(tmp_path / "disabled-metrics.db"), metrics_enabled=False)
    )
    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 404


def test_validation_errors_use_problem_details(tmp_path) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "validation.db")))
    with TestClient(app) as client:
        response = client.post(
            "/v1/chat",
            json={"session_id": "bad id", "message": "hello"},
            headers={"X-Request-ID": "validation_12345"},
        )
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["request_id"] == "validation_12345"
    assert response.json()["errors"]


def test_unexpected_errors_return_safe_problem_details(tmp_path, monkeypatch) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "unexpected.db")))
    with TestClient(app, raise_server_exceptions=False) as client:
        monkeypatch.setattr(
            app.state.service,
            "respond",
            lambda *_: (_ for _ in ()).throw(RuntimeError("private implementation detail")),
        )
        response = client.post(
            "/v1/chat",
            json={"session_id": "unexpected-session-1", "message": "hello"},
        )

    assert response.status_code == 500
    assert response.json()["title"] == "Internal server error"
    assert "private implementation detail" not in response.text
