from __future__ import annotations

import os
import re
from dataclasses import dataclass

DEFAULT_APP_ENV = "development"
DEFAULT_DATABASE_PATH = "./data/concierge.db"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "json"
DEFAULT_OLLAMA_MODEL = "qwen3:14b"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 45.0
DEFAULT_ALLOWED_HOSTS = ("localhost", "127.0.0.1", "testserver")


class ConfigurationError(ValueError):
    """Raised when runtime configuration is unsafe or malformed."""


def _parse_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be a boolean")


def _parse_csv(value: str | None, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if value is None:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _parse_positive_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a number") from exc
    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str = DEFAULT_APP_ENV
    database_path: str = DEFAULT_DATABASE_PATH
    log_level: str = DEFAULT_LOG_LEVEL
    log_format: str = DEFAULT_LOG_FORMAT
    api_key_hashes: tuple[str, ...] = ()
    allowed_hosts: tuple[str, ...] = DEFAULT_ALLOWED_HOSTS
    metrics_enabled: bool = True
    docs_enabled: bool = True
    ollama_base_url: str | None = None
    ollama_model: str = DEFAULT_OLLAMA_MODEL
    ollama_timeout_seconds: float = DEFAULT_OLLAMA_TIMEOUT_SECONDS

    def validate(self) -> Settings:
        if self.app_env not in {"development", "test", "production"}:
            raise ConfigurationError("APP_ENV must be development, test, or production")
        if self.log_format not in {"json", "plain"}:
            raise ConfigurationError("LOG_FORMAT must be json or plain")
        if self.log_level.upper() not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigurationError("LOG_LEVEL is invalid")
        if self.ollama_timeout_seconds <= 0:
            raise ConfigurationError("OLLAMA_TIMEOUT_SECONDS must be greater than zero")
        if not self.allowed_hosts:
            raise ConfigurationError("ALLOWED_HOSTS must contain at least one host")
        for key_hash in self.api_key_hashes:
            if re.fullmatch(r"[0-9a-fA-F]{64}", key_hash) is None:
                raise ConfigurationError("API_KEY_HASHES entries must be SHA-256 hex digests")
        if self.app_env == "production" and not self.api_key_hashes:
            raise ConfigurationError("API_KEY_HASHES is required in production")
        return self

    @classmethod
    def from_environment(cls) -> Settings:
        app_env = os.getenv("APP_ENV", DEFAULT_APP_ENV).strip().lower()
        return cls(
            app_env=app_env,
            database_path=os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH),
            log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
            log_format=os.getenv("LOG_FORMAT", DEFAULT_LOG_FORMAT).lower(),
            api_key_hashes=_parse_csv(os.getenv("API_KEY_HASHES")),
            allowed_hosts=_parse_csv(os.getenv("ALLOWED_HOSTS"), DEFAULT_ALLOWED_HOSTS),
            metrics_enabled=_parse_bool("METRICS_ENABLED", True),
            docs_enabled=_parse_bool("DOCS_ENABLED", app_env != "production"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL") or None,
            ollama_model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            ollama_timeout_seconds=_parse_positive_float(
                "OLLAMA_TIMEOUT_SECONDS", DEFAULT_OLLAMA_TIMEOUT_SECONDS
            ),
        ).validate()
