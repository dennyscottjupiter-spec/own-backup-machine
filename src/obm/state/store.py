# ---
# purpose: atomic JSON read/write of AppState under the data dir
# exports: load(), save()
# depends: paths.py, schema.py
# gotcha: writes to a tmp file then os.replace — a crash mid-write leaves the old state intact
# ---
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from .. import paths
from .schema import AppState, SCHEMA_VERSION, VolumeState

STATE_FILENAME = "state.json"


def _state_path() -> Path:
    return paths.data_dir() / STATE_FILENAME


def load() -> AppState:
    p = _state_path()
    if not p.exists():
        return AppState()
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AppState()

    volumes = {k: VolumeState(**v) for k, v in raw.get("volumes", {}).items()}
    return AppState(
        schema_version=raw.get("schema_version", SCHEMA_VERSION),
        volumes=volumes,
        last_scan_files=int(raw.get("last_scan_files", 0)),
    )


def save(state: AppState) -> None:
    paths.ensure_data_dir()
    target = _state_path()
    fd, tmp_path = tempfile.mkstemp(dir=str(target.parent), prefix=".state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "schema_version": state.schema_version,
                    "volumes": {k: asdict(v) for k, v in state.volumes.items()},
                    "last_scan_files": state.last_scan_files,
                },
                f,
                indent=2,
            )
        os.replace(tmp_path, target)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
