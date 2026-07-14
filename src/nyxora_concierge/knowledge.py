from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib.resources import files

TOKEN_PATTERN = re.compile(r"[a-z0-9-]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "for",
    "how",
    "i",
    "is",
    "it",
    "me",
    "my",
    "of",
    "recommend",
    "recommendation",
    "recommending",
    "the",
    "to",
    "what",
    "you",
}


@dataclass(frozen=True, slots=True)
class KnowledgeEntry:
    entry_id: str
    title: str
    content: str
    tags: tuple[str, ...]


def _tokens(value: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(value.casefold()) if token not in STOP_WORDS}


class KnowledgeBase:
    def __init__(self, entries: tuple[KnowledgeEntry, ...]):
        self.entries = entries

    @classmethod
    def from_package(cls) -> KnowledgeBase:
        data_path = files("nyxora_concierge").joinpath("data/knowledge_base.json")
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        entries = tuple(
            KnowledgeEntry(
                entry_id=item["id"],
                title=item["title"],
                content=item["content"],
                tags=tuple(item["tags"]),
            )
            for item in payload
        )
        return cls(entries)

    def search(self, query: str, limit: int = 2) -> list[KnowledgeEntry]:
        query_tokens = _tokens(query)
        ranked: list[tuple[int, KnowledgeEntry]] = []
        for entry in self.entries:
            title_and_tags = _tokens(f"{entry.title} {' '.join(entry.tags)}")
            content_tokens = _tokens(entry.content)
            score = (3 * len(query_tokens & title_and_tags)) + len(query_tokens & content_tokens)
            if score:
                ranked.append((score, entry))
        ranked.sort(key=lambda item: (-item[0], item[1].entry_id))
        return [entry for _, entry in ranked[:limit]]
