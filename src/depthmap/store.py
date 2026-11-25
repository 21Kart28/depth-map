from collections import Counter
from typing import Protocol

from depthmap.models import Entry


class Repository(Protocol):
    """Where entries are kept. list() returns the newest first."""

    def add(self, entry: Entry) -> Entry: ...

    def get(self, entry_id: str) -> Entry | None: ...

    def count_by_question(self, client_id: str) -> dict[str, int]: ...

    def list(self, limit: int = 20) -> list[Entry]: ...


class InMemoryRepository:
    def __init__(self):
        self._entries = []

    def add(self, entry: Entry) -> Entry:
        self._entries.append(entry)
        return entry

    def get(self, entry_id: str) -> Entry | None:
        return next((entry for entry in self._entries if entry.id == entry_id), None)

    def count_by_question(self, client_id: str) -> dict[str, int]:
        return dict(Counter(e.question_id for e in self._entries if e.client_id == client_id))

    def list(self, limit: int = 20) -> list[Entry]:
        # sorted() keeps equal items in the order it got them, so reversing first puts the
        # later insert ahead when two entries share a timestamp
        newest_first = sorted(reversed(self._entries), key=lambda e: e.created_at, reverse=True)
        return newest_first[:limit]
