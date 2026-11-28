import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient
from test_store import make_entry

from depthmap.api import create_app
from depthmap.cli import main
from depthmap.config import Settings
from depthmap.db import OldSchemaError, connect
from depthmap.providers import FakeProvider
from depthmap.store_sqlite import SQLiteRepository

# the entries table as it was before codebook_version was added
OLD_ENTRIES = """
CREATE TABLE entries (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    provider TEXT NOT NULL,
    embedding BLOB
);
"""


@pytest.fixture
def old_path(tmp_path):
    path = str(tmp_path / "old.db")
    with closing(sqlite3.connect(path)) as db:
        db.executescript(OLD_ENTRIES)
    return path


def test_new_file_gets_the_tables(tmp_path):
    with closing(connect(str(tmp_path / "new.db"))) as db:
        rows = db.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    assert {row["name"] for row in rows} == {"questions", "entries", "analyses"}


def test_old_schema_is_refused(old_path):
    with pytest.raises(OldSchemaError) as raised:
        connect(old_path)
    assert str(raised.value) == f"{old_path} has an old schema, delete the file"


def test_old_schema_stops_every_store_call(old_path):
    repo = SQLiteRepository(old_path)
    for call in (repo.list, lambda: repo.get("x"), lambda: repo.add(make_entry())):
        with pytest.raises(OldSchemaError):
            call()


def test_api_reports_an_old_schema(old_path, settings):
    app = create_app(settings=settings, provider=FakeProvider(), repo=SQLiteRepository(old_path))
    reply = TestClient(app).get("/entries")
    assert reply.status_code == 500
    assert reply.json() == {
        "error": "old_schema",
        "detail": f"{old_path} has an old schema, delete the file",
    }


def test_cli_prints_an_old_schema_and_exits(old_path, monkeypatch):
    monkeypatch.setenv("DEPTHMAP_DB_PATH", old_path)
    monkeypatch.setattr("sys.argv", ["depthmap"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == f"{old_path} has an old schema, delete the file"


def test_building_the_app_does_not_create_the_file(tmp_path):
    path = tmp_path / "unused.db"
    create_app(settings=Settings(_env_file=None, provider="fake", db_path=str(path)))
    assert not path.exists()
