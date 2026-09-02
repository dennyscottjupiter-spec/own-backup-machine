# ---
# purpose: sqlite index of files actually archived — path_key -> size, mtime_ns, hash
# exports: Fingerprints
# depends: paths.py
# gotcha: only holds files actually archived; a JSON index of 200k rows would be rewritten wholesale every run
# ---
from __future__ import annotations

import sqlite3
from pathlib import Path

from .. import paths

DB_FILENAME = "fingerprints.sqlite3"

_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS files ("
    "path_key TEXT PRIMARY KEY, size INTEGER, mtime_ns INTEGER, "
    "hash TEXT, last_seen_run TEXT)"
)


class Fingerprints:
    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            paths.ensure_data_dir()
            db_path = paths.data_dir() / DB_FILENAME
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def lookup(self, path: str) -> tuple[int, int, str] | None:
        row = self._conn.execute(
            "SELECT size, mtime_ns, hash FROM files WHERE path_key = ?", (path.lower(),)
        ).fetchone()
        return tuple(row) if row else None

    def upsert(self, path: str, size: int, mtime_ns: int, content_hash: str, run_id: str) -> None:
        self._conn.execute(
            "INSERT INTO files (path_key, size, mtime_ns, hash, last_seen_run) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(path_key) DO UPDATE SET "
            "size=excluded.size, mtime_ns=excluded.mtime_ns, "
            "hash=excluded.hash, last_seen_run=excluded.last_seen_run",
            (path.lower(), size, mtime_ns, content_hash, run_id),
        )

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Fingerprints":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.commit()
        self.close()
