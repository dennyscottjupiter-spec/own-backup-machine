# ---
# purpose: the persisted state shape — per-volume USN cursor + last successful run
# exports: SCHEMA_VERSION, VolumeState, AppState
# gotcha: keyed by volume GUID path, never by drive letter — letters get reassigned.
#         last_scan_files is only how many files the previous scan walked past: it feeds the
#         scan percentage in the UI and must never gate what a scan yields
# ---
from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = 1


@dataclass(slots=True)
class VolumeState:
    guid_path: str
    letter: str
    last_run_utc: str
    journal_id: int = 0
    next_usn: int = 0


@dataclass(slots=True)
class AppState:
    schema_version: int = SCHEMA_VERSION
    volumes: dict[str, VolumeState] = field(default_factory=dict)
    last_scan_files: int = 0
