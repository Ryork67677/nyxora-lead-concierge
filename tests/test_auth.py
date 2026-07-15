import hashlib

import pytest
from fastapi.testclient import TestClient

from nyxora_concierge.config import ConfigurationError, Settings
from nyxora_concierge.main import create_app

TEST_KEY = "portfolio-production-key"
TEST_KEY_HASH = hashlib.sha256(TEST_KEY.encode()).hexdigest()


def _secured_settings(tmp_path) -> Settings:
    return Settings(
        app_env="production",
        database_path=str(tmp_path / "secured.db"),
        api_key_hashes=(TEST_KEY_HASH,),
        docs_enabled=False,
    )


def _chat_payload() -> dict[str, object]:
    return {
        "session_id": "secured-session-123",
        "message": "I want to book a consultation",
        "consent_to_store": False,
    }


def test_production_requires_api_key_hashes(tmp_path) -> None:
    with pytest.raises(ConfigurationError, match="API_KEY_HASHES"):
        create_app(Settings(app_env="production", database_path=str(tmp_path / "unsafe.db")))


def test_malformed_api_key_hash_is_rejected(tmp_path) -> None:
    with pytest.raises(ConfigurationError, match="SHA-256"):
        create_app(
            Settings(
                database_path=str(tmp_path / "invalid.db"),
                api_key_hashes=("not-a-hash",),
            )
        )


@pytest.mark.parametrize("authorization", [None, "Bearer wrong-key", "Basic abc123"])
def test_chat_rejects_missing_or_invalid_credentials(tmp_path, authorization) -> None:
    app = create_app(_secured_settings(tmp_path))
    headers = {"Authorization": authorization} if authorization else {}
    with TestClient(app) as client:
        response = client.post("/v1/chat", json=_chat_payload(), headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Authentication required"
    assert response.json()["request_id"] == response.headers["x-request-id"]


def test_valid_bearer_key_allows_chat(tmp_path) -> None:
    app = create_app(_secured_settings(tmp_path))
    with TestClient(app) as client:
        response = client.post(
            "/v1/chat",
            json=_chat_payload(),
            headers={"Authorization": f"Bearer {TEST_KEY}"},
        )

    assert response.status_code == 200
    assert response.json()["recommended_action"] == "book_consultation"


def test_liveness_remains_available_without_credentials(tmp_path) -> None:
    app = create_app(_secured_settings(tmp_path))
    with TestClient(app) as client:
        response = client.get("/livez")
    assert response.status_code == 200


def test_production_disables_docs_when_configured(tmp_path) -> None:
    app = create_app(_secured_settings(tmp_path))
    with TestClient(app) as client:
        response = client.get("/docs")
    assert response.status_code == 404
