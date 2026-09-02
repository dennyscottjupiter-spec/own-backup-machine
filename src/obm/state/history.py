# ---
# purpose: past runs — list, locate, delete (deleting also removes the archive file)
# exports: load(), append(), locate(), delete()
# depends: paths.py, models.RunRecord
# ---
from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from .. import paths
from ..models import RunRecord

HISTORY_FILENAME = "history.json"


def _history_path() -> Path:
    return paths.data_dir() / HISTORY_FILENAME


def load() -> list[RunRecord]:
    p = _history_path()
    if not p.exists():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [RunRecord(**r) for r in raw]


def _save(records: list[RunRecord]) -> None:
    paths.ensure_data_dir()
    _history_path().write_text(
        json.dumps([asdict(r) for r in records], indent=2), encoding="utf-8"
    )


def append(record: RunRecord) -> None:
    records = load()
    records.append(record)
    _save(records)


def locate(run_id: str) -> RunRecord | None:
    return next((r for r in load() if r.run_id == run_id), None)


def delete(run_id: str, delete_archive_file: bool = True) -> bool:
    records = load()
    target = next((r for r in records if r.run_id == run_id), None)
    if target is None:
        return False

    if delete_archive_file and target.archive_path and os.path.exists(target.archive_path):
        os.remove(target.archive_path)

    _save([r for r in records if r.run_id != run_id])
    return True
