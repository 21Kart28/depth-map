from test_store import make_entry

from depthmap.store_sqlite import SQLiteRepository


def test_entries_survive_a_restart(tmp_path):
    path = str(tmp_path / "test.db")
    entry = SQLiteRepository(path).add(make_entry())
    reopened = SQLiteRepository(path)
    assert reopened.get(entry.id) == entry
    assert reopened.list() == [entry]
