from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from .models import ChatResponse


class RepositoryError(RuntimeError):
    """Raised when consent-gated application state cannot be read or written."""


class EventRepository:
    """Stores outcome metadata only; raw chat messages and session IDs are not retained."""

    def __init__(self, database_path: str):
        self.database_path = database_path

    def initialize(self) -> None:
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with closing(sqlite3.connect(path, timeout=5)) as connection:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversation_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_hash TEXT NOT NULL,
                        intent TEXT NOT NULL,
                        qualification_score INTEGER NOT NULL,
                        recommended_action TEXT NOT NULL,
                        requires_human INTEGER NOT NULL,
                        safety_flags TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
        except (OSError, sqlite3.Error) as exc:
            raise RepositoryError("Database initialization failed") from exc

    def check(self) -> None:
        try:
            with closing(sqlite3.connect(self.database_path, timeout=2)) as connection:
                schema = connection.execute(
                    """
                    SELECT 1 FROM sqlite_master
                    WHERE type = 'table' AND name = 'conversation_events'
                    """
                ).fetchone()
        except sqlite3.Error as exc:
            raise RepositoryError("Database readiness check failed") from exc
        if schema is None:
            raise RepositoryError("Database schema is unavailable")

    def record(self, session_id: str, result: ChatResponse) -> None:
        session_hash = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
        try:
            with closing(sqlite3.connect(self.database_path, timeout=5)) as connection:
                connection.execute(
                    """
                    INSERT INTO conversation_events (
                        session_hash, intent, qualification_score, recommended_action,
                        requires_human, safety_flags, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_hash,
                        result.intent.value,
                        result.qualification_score,
                        result.recommended_action.value,
                        int(result.requires_human),
                        ",".join(result.safety_flags),
                        datetime.now(UTC).isoformat(),
                    ),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise RepositoryError("Database write failed") from exc
