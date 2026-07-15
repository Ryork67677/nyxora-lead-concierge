import pytest

from nyxora_concierge.config import ConfigurationError, Settings


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("app_env", "staging", "APP_ENV"),
        ("log_format", "xml", "LOG_FORMAT"),
        ("log_level", "LOUD", "LOG_LEVEL"),
        ("ollama_timeout_seconds", 0, "OLLAMA_TIMEOUT_SECONDS"),
        ("allowed_hosts", (), "ALLOWED_HOSTS"),
    ],
)
def test_invalid_settings_are_rejected(field, value, message) -> None:
    values = {field: value}
    with pytest.raises(ConfigurationError, match=message):
        Settings(**values).validate()


def test_environment_parses_runtime_controls(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_FORMAT", "plain")
    monkeypatch.setenv("ALLOWED_HOSTS", "api.example.com, localhost")
    monkeypatch.setenv("METRICS_ENABLED", "false")
    monkeypatch.setenv("DOCS_ENABLED", "true")
    settings = Settings.from_environment()
    assert settings.app_env == "test"
    assert settings.allowed_hosts == ("api.example.com", "localhost")
    assert settings.metrics_enabled is False
    assert settings.docs_enabled is True


def test_invalid_environment_boolean_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("METRICS_ENABLED", "sometimes")
    with pytest.raises(ConfigurationError, match="METRICS_ENABLED"):
        Settings.from_environment()


@pytest.mark.parametrize("value", ["fast", "0", "-1"])
def test_invalid_environment_timeout_is_rejected(monkeypatch, value) -> None:
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", value)
    with pytest.raises(ConfigurationError, match="OLLAMA_TIMEOUT_SECONDS"):
        Settings.from_environment()
