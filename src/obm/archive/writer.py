# ---
# purpose: build locally -> add the README -> verify -> copy -> .part -> os.replace — the
#          crash-safe archive write
# exports: write_archive(), cleanup_stale_parts()
# depends: detect.DetectedTool, sevenzip.py, winrar.py, zipfallback.py, readme.py
# gotcha: compress on local disk THEN copy to the destination — a mid-compress failure over SMB
#         would leave an unverifiable file; os.replace on the destination volume is atomic.
#         The README goes in BEFORE verify(), so a broken readme add can never ship
# ---
from __future__ import annotations

import os
import shutil
import tempfile
from typing import Callable

from . import readme as readme_mod
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


def _add_readme(backend, tool: DetectedTool, level: int, staging: str, readme_text: str) -> None:
    readme_path = readme_mod.write_temp(readme_text)
    try:
        backend.add_readme(tool.exe_path, level, staging, readme_path)
    finally:
        shutil.rmtree(os.path.dirname(readme_path), ignore_errors=True)


def write_archive(
    tool: DetectedTool,
    level: int,
    files: list[str],
    dest_dir: str,
    archive_filename: str,
    on_progress: Callable[[int, int], None] | None = None,
    on_stage: Callable[[str], None] | None = None,
    readme_text: str = "",
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
        if readme_text:
            say(f"Adding {readme_mod.README_NAME}")
            _add_readme(backend, tool, level, staging, readme_text)
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
