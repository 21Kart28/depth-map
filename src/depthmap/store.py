from typing import Protocol

from depthmap.config import Settings
from depthmap.db import OldSchemaError
from depthmap.models import DEFAULT_CLIENT_ID, Entry
from depthmap.store_sqlite import SQLiteRepository

# OldSchemaError is passed on from db.py so callers get everything about storage from here
__all__ = ["InMemoryRepository", "OldSchemaError", "Repository", "get_repository"]


class Repository(Protocol):
    """Where entries are kept. For one client, list() is newest first, question_history() oldest."""

    def add(self, entry: Entry) -> Entry: ...

    def get(self, entry_id: str) -> Entry | None: ...

    def question_history(self, client_id: str) -> list[str]: ...

    def list(self, client_id: str = DEFAULT_CLIENT_ID, limit: int = 20) -> list[Entry]: ...


class InMemoryRepository:
    def __init__(self):
        self._entries = []

    def add(self, entry: Entry) -> Entry:
        self._entries.append(entry)
        return entry

    def get(self, entry_id: str) -> Entry | None:
        return next((entry for entry in self._entries if entry.id == entry_id), None)

    def question_history(self, client_id: str) -> list[str]:
        mine = [e for e in self._entries if e.client_id == client_id]
        return [e.question_id for e in sorted(mine, key=lambda e: e.created_at)]

    def list(self, client_id: str = DEFAULT_CLIENT_ID, limit: int = 20) -> list[Entry]:
        mine = [e for e in self._entries if e.client_id == client_id]
        # sorted() keeps equal items in the order it got them, so reversing first puts the
        # later insert ahead when two entries share a timestamp
        newest_first = sorted(reversed(mine), key=lambda e: e.created_at, reverse=True)
        return newest_first[:limit]


def get_repository(settings: Settings) -> Repository:
    return SQLiteRepository(settings.db_path)
