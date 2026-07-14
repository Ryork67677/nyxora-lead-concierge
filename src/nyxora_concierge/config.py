from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_APP_ENV = "development"
DEFAULT_DATABASE_PATH = "./data/concierge.db"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_OLLAMA_MODEL = "qwen3:14b"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 45.0


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str = DEFAULT_APP_ENV
    database_path: str = DEFAULT_DATABASE_PATH
    log_level: str = DEFAULT_LOG_LEVEL
    ollama_base_url: str | None = None
    ollama_model: str = DEFAULT_OLLAMA_MODEL
    ollama_timeout_seconds: float = DEFAULT_OLLAMA_TIMEOUT_SECONDS

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            app_env=os.getenv("APP_ENV", DEFAULT_APP_ENV),
            database_path=os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH),
            log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL") or None,
            ollama_model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            ollama_timeout_seconds=float(
                os.getenv("OLLAMA_TIMEOUT_SECONDS", str(DEFAULT_OLLAMA_TIMEOUT_SECONDS))
            ),
        )
