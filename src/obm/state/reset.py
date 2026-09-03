# ---
# purpose: forget the delta baseline so the next run considers every file again
# exports: reset()
# depends: paths.py, store.py, fingerprints.py, carryover.py
# gotcha: history.json is deliberately kept -- it is the run log, not a baseline
# ---
from __future__ import annotations

from pathlib import Path

from .. import paths
from .carryover import CARRYOVER_FILENAME
from .fingerprints import DB_FILENAME
from .store import STATE_FILENAME

BASELINE_FILES = (STATE_FILENAME, DB_FILENAME, CARRYOVER_FILENAME)


def reset() -> list[Path]:
    """Delete the baseline files that exist; returns the ones actually removed."""
    removed = []
    for name in BASELINE_FILES:
        p = paths.data_dir() / name
        if p.exists():
            p.unlink()
            removed.append(p)
    return removed
