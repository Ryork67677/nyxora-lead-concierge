from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_APP_ENV = "development"
DEFAULT_DATABASE_PATH = "./data/concierge.db"
DEFAULT_LOG_LEVEL = "INFO"


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str = DEFAULT_APP_ENV
    database_path: str = DEFAULT_DATABASE_PATH
    log_level: str = DEFAULT_LOG_LEVEL

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            app_env=os.getenv("APP_ENV", DEFAULT_APP_ENV),
            database_path=os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH),
            log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL),
        )
