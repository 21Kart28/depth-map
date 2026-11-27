import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    category TEXT
);
CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    codebook_version TEXT NOT NULL,
    provider TEXT NOT NULL,
    embedding BLOB
);
CREATE TABLE IF NOT EXISTS analyses (
    entry_id TEXT PRIMARY KEY REFERENCES entries (id),
    payload TEXT NOT NULL
);
"""


def connect(path: str) -> sqlite3.Connection:
    """Open the database file and create the tables if they are missing."""
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db
