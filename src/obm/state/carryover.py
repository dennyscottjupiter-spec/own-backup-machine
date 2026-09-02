# ---
# purpose: files skipped for lock/denial, force-reinjected next run regardless of cursor/mtime
# exports: CarryEntry, load(), save(), record(), to_candidates()
# depends: paths.py, models.CandidateFile, winapi.longpath
# gotcha: this is a correctness requirement — without it a USN cursor advances past a locked
#         file and it is lost forever, since the file's own change events are gone from the journal
# ---
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .. import paths
from ..models import CandidateFile
from ..winapi.longpath import to_extended

CARRYOVER_FILENAME = "carryover.json"


@dataclass(slots=True)
class CarryEntry:
    path: str
    reason: str  # "locked" | "denied"


def _carryover_path() -> Path:
    return paths.data_dir() / CARRYOVER_FILENAME


def load() -> list[CarryEntry]:
    p = _carryover_path()
    if not p.exists():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [CarryEntry(**e) for e in raw]


def save(entries: list[CarryEntry]) -> None:
    paths.ensure_data_dir()
    p = _carryover_path()
    p.write_text(
        json.dumps([{"path": e.path, "reason": e.reason} for e in entries], indent=2),
        encoding="utf-8",
    )


def record(entries: list[CarryEntry], path: str, reason: str) -> list[CarryEntry]:
    updated = [e for e in entries if e.path.lower() != path.lower()]
    updated.append(CarryEntry(path=path, reason=reason))
    return updated


def to_candidates(entries: list[CarryEntry]) -> Iterator[CandidateFile]:
    for e in entries:
        try:
            st = os.stat(to_extended(e.path))
        except OSError:
            continue
        yield CandidateFile(
            path=e.path,
            volume=os.path.splitdrive(e.path)[0].upper(),
            size=st.st_size,
            mtime_ns=st.st_mtime_ns,
            attributes=st.st_file_attributes,
            source="carryover",
            tags=frozenset({e.reason}),
        )
