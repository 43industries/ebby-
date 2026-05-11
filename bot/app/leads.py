"""SQLite-backed lead storage.

Intentionally tiny - one table, two functions. SQLite is plenty for the
expected volume; swap to Postgres later by replacing this module.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List

from .config import get_settings
from .schemas import LeadRecord


SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    phone       TEXT NOT NULL,
    email       TEXT NOT NULL,
    service     TEXT NOT NULL,
    details     TEXT NOT NULL,
    source      TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
"""


def _db_path() -> Path:
    p = Path(get_settings().db_path)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent.parent / p
    return p


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(SCHEMA)


def save_lead(
    *,
    name: str,
    phone: str,
    email: str,
    service: str,
    details: str,
    source: str = "unknown",
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO leads (name, phone, email, service, details, source, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, phone, email, service, details, source, created_at),
        )
        return int(cur.lastrowid)


def list_leads(limit: int = 100) -> List[LeadRecord]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, phone, email, service, details, source, created_at "
            "FROM leads ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [LeadRecord(**dict(r)) for r in rows]
