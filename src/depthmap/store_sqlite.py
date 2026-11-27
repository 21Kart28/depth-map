from contextlib import closing
from datetime import UTC

from depthmap.db import connect
from depthmap.models import Analysis, Entry

SELECT_ENTRY = """
SELECT e.id, e.client_id, e.question_id, e.question_text, e.response, e.created_at,
       e.prompt_version, e.codebook_version, e.provider, a.payload
FROM entries e JOIN analyses a ON a.entry_id = e.id
"""


def to_entry(row) -> Entry:
    fields = dict(row)
    analysis = Analysis.model_validate_json(fields.pop("payload"))
    return Entry(analysis=analysis, **fields)


class SQLiteRepository:
    def __init__(self, path: str):
        self.path = path

    def add(self, entry: Entry) -> Entry:
        # a connection per call: the API runs each request in a worker thread and a sqlite3
        # connection belongs to the thread that opened it
        with closing(connect(self.path)) as db, db:
            db.execute(
                "INSERT INTO entries (id, client_id, question_id, question_text, response,"
                " created_at, prompt_version, codebook_version, provider)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entry.id,
                    entry.client_id,
                    entry.question_id,
                    entry.question_text,
                    entry.response,
                    # one fixed format in UTC, so sorting the text sorts by time
                    entry.created_at.astimezone(UTC).isoformat(timespec="microseconds"),
                    entry.prompt_version,
                    entry.codebook_version,
                    entry.provider,
                ),
            )
            db.execute(
                "INSERT INTO analyses (entry_id, payload) VALUES (?, ?)",
                (entry.id, entry.analysis.model_dump_json()),
            )
        return entry

    def get(self, entry_id: str) -> Entry | None:
        with closing(connect(self.path)) as db:
            row = db.execute(SELECT_ENTRY + "WHERE e.id = ?", (entry_id,)).fetchone()
        return to_entry(row) if row else None

    def question_history(self, client_id: str) -> list[str]:
        with closing(connect(self.path)) as db:
            rows = db.execute(
                "SELECT question_id FROM entries WHERE client_id = ? ORDER BY created_at, rowid",
                (client_id,),
            ).fetchall()
        return [row["question_id"] for row in rows]

    def list(self, limit: int = 20) -> list[Entry]:
        with closing(connect(self.path)) as db:
            rows = db.execute(
                SELECT_ENTRY + "ORDER BY e.created_at DESC, e.rowid DESC LIMIT ?", (limit,)
            ).fetchall()
        return [to_entry(row) for row in rows]
