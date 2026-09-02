# ---
# purpose: per-volume-GUID cursor bookkeeping + the USN validity decision, a pure function
# exports: decide(), walk_cutoff_ns(), now_iso(), mark_run()
# depends: schema.py
# gotcha: decide() takes no ctypes/journal handle — this is why it's testable with zero USN code
# ---
from __future__ import annotations

from datetime import datetime, timezone

from .schema import AppState, VolumeState


def decide(
    stored: VolumeState | None,
    queried_journal_id: int,
    queried_lowest_valid_usn: int,
    queried_next_usn: int,
) -> tuple[str, str]:
    if stored is None:
        return "walk", "first run"
    if stored.journal_id != queried_journal_id:
        return "walk", "journal recreated"
    if stored.next_usn < queried_lowest_valid_usn:
        return "walk", "journal wrapped past cursor"
    if stored.next_usn > queried_next_usn:
        return "walk", "journal rewound"
    return "usn", "cursor valid"


def walk_cutoff_ns(stored: VolumeState | None) -> int:
    if stored is None or not stored.last_run_utc:
        return 0
    dt = datetime.fromisoformat(stored.last_run_utc)
    return int(dt.timestamp() * 1_000_000_000)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def mark_run(
    state: AppState,
    guid_path: str,
    letter: str,
    run_utc: str,
    journal_id: int = 0,
    next_usn: int = 0,
) -> None:
    state.volumes[guid_path] = VolumeState(
        guid_path=guid_path,
        letter=letter,
        last_run_utc=run_utc,
        journal_id=journal_id,
        next_usn=next_usn,
    )
