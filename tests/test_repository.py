import sqlite3
from contextlib import closing

from nyxora_concierge.knowledge import KnowledgeBase
from nyxora_concierge.models import ChatRequest
from nyxora_concierge.repository import EventRepository
from nyxora_concierge.service import ConciergeService


def test_storage_requires_consent_and_hashes_session(tmp_path) -> None:
    database = tmp_path / "events.db"
    repository = EventRepository(str(database))
    repository.initialize()
    service = ConciergeService(KnowledgeBase.from_package(), repository)

    not_stored = service.respond(
        ChatRequest(session_id="private-session-1", message="Book a consultation")
    )
    stored = service.respond(
        ChatRequest(
            session_id="private-session-2",
            message="Book a consultation",
            consent_to_store=True,
        )
    )

    with closing(sqlite3.connect(database)) as connection:
        rows = connection.execute(
            "SELECT session_hash, intent, qualification_score FROM conversation_events"
        ).fetchall()

    assert not_stored.stored is False
    assert stored.stored is True
    assert len(rows) == 1
    assert rows[0][0] != "private-session-2"
    assert len(rows[0][0]) == 64
    assert rows[0][1] == "booking"
