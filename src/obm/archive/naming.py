# ---
# purpose: archive filenames, run ids, and the drive-letter-safe entry name used by the zip fallback
# exports: archive_name(), run_id_for(), arcname_for()
# gotcha: arcname_for() is only for zipfallback — 7z/WinRAR keep the real path via -spf2/full-path
# ---
from __future__ import annotations

import os
from datetime import datetime

_EXT_BY_TOOL = {"7z": ".7z", "rar": ".rar", "zip": ".zip"}


def run_id_for(when: datetime | None = None) -> str:
    when = when or datetime.now()
    # millisecond suffix: two manual runs seconds apart never collide, but two runs
    # inside the same test process (or a fast retry) must not silently overwrite.
    return when.strftime("%Y%m%d_%H%M%S") + f"_{when.microsecond // 1000:03d}"


def archive_name(tool_name: str, when: datetime | None = None) -> str:
    ext = _EXT_BY_TOOL.get(tool_name, ".zip")
    return f"own-backup-machine_{run_id_for(when)}{ext}"


def arcname_for(path: str) -> str:
    drive, rest = os.path.splitdrive(path)
    drive = drive.rstrip(":")
    return f"{drive}{rest}".replace("\\", "/").lstrip("/")
