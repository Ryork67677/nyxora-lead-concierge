import json
import re

from fastapi.testclient import TestClient

from nyxora_concierge.config import Settings
from nyxora_concierge.main import create_app


def test_valid_request_id_is_propagated(tmp_path) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "request-id.db")))
    with TestClient(app) as client:
        response = client.get("/livez", headers={"X-Request-ID": "request_12345678"})
    assert response.headers["x-request-id"] == "request_12345678"


def test_invalid_request_id_is_replaced(tmp_path) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "request-id.db")))
    with TestClient(app) as client:
        response = client.get("/livez", headers={"X-Request-ID": "bad value!"})
    generated = response.headers["x-request-id"]
    assert generated != "bad value!"
    assert re.fullmatch(r"[0-9a-f]{32}", generated)


def test_json_request_logs_do_not_contain_credentials_or_messages(tmp_path, capsys) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "logs.db"), log_format="json"))
    secret = "never-log-this-token"
    visitor_message = "private visitor wording should not be logged"
    with TestClient(app) as client:
        client.post(
            "/v1/chat",
            json={"session_id": "logging-session-1", "message": visitor_message},
            headers={"Authorization": f"Bearer {secret}"},
        )

    output = capsys.readouterr().out
    records = [json.loads(line) for line in output.splitlines() if line.strip()]
    request_logs = [record for record in records if record["event"] == "http_request_completed"]
    assert request_logs
    assert request_logs[0]["path"] == "/v1/chat"
    assert request_logs[0]["status_code"] == 200
    assert secret not in output
    assert visitor_message not in output


def test_plain_logging_includes_request_context(tmp_path, capsys) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "plain.db"), log_format="plain"))
    with TestClient(app) as client:
        client.get("/livez", headers={"X-Request-ID": "plain_request_123"})
    assert "request_id=plain_request_123" in capsys.readouterr().out


def test_untrusted_host_is_rejected(tmp_path) -> None:
    app = create_app(Settings(database_path=str(tmp_path / "hosts.db")))
    with TestClient(app) as client:
        response = client.get("/livez", headers={"Host": "evil.example"})
    assert response.status_code == 400
