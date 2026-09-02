# ---
# purpose: build locally -> verify -> copy -> .part -> os.replace — the crash-safe archive write
# exports: write_archive(), cleanup_stale_parts()
# depends: detect.DetectedTool, sevenzip.py, winrar.py, zipfallback.py
# gotcha: compress on local disk THEN copy to the destination — a mid-compress failure over SMB
#         would leave an unverifiable file; os.replace on the destination volume is atomic
# ---
from __future__ import annotations

import os
import shutil
import tempfile
from typing import Callable

from . import sevenzip, winrar, zipfallback
from .detect import DetectedTool

_BACKENDS = {"7z": sevenzip, "rar": winrar, "zip": zipfallback}


def cleanup_stale_parts(dest_dir: str) -> list[str]:
    removed: list[str] = []
    if not os.path.isdir(dest_dir):
        return removed
    for name in os.listdir(dest_dir):
        if name.endswith(".part"):
            full = os.path.join(dest_dir, name)
            try:
                os.remove(full)
                removed.append(full)
            except OSError:
                pass
    return removed


def write_archive(
    tool: DetectedTool,
    level: int,
    files: list[str],
    dest_dir: str,
    archive_filename: str,
    on_progress: Callable[[int, int], None] | None = None,
    on_stage: Callable[[str], None] | None = None,
) -> str:
    backend = _BACKENDS[tool.name]
    os.makedirs(dest_dir, exist_ok=True)

    final = os.path.join(dest_dir, archive_filename)
    partial = final + ".part"
    staging = os.path.join(tempfile.gettempdir(), archive_filename)

    def say(text: str) -> None:
        if on_stage:
            on_stage(text)

    say(f"Compressing {len(files)} files to {staging}")
    backend.create(tool.exe_path, level, staging, files, on_progress)
    try:
        say("Verifying the archive")
        if not backend.verify(tool.exe_path, staging):
            raise RuntimeError("archive failed verification, aborting")
        say(f"Copying to {dest_dir}")
        shutil.copyfile(staging, partial)
        say("Renaming into place")
        os.replace(partial, final)
    finally:
        if os.path.exists(staging):
            os.remove(staging)

    return final
