# ---
# purpose: WinRAR backend — same create()/verify() signature as sevenzip.py and zipfallback.py
# exports: create(), verify()
# depends: listfile.py
# gotcha: the listfile MUST be UTF-16LE with a BOM — WinRAR silently mangles UTF-8 listfiles
# ---
from __future__ import annotations

import os
import subprocess
from typing import Callable

from .listfile import write_winrar_listfile


def create(
    exe_path: str,
    level: int,
    out_path: str,
    files: list[str],
    on_progress: Callable[[int, int], None] | None = None,
) -> None:
    listfile = write_winrar_listfile(files)
    try:
        cmd = [exe_path, "a", f"-m{level}", "-ep3", out_path, f"@{listfile}"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(f"rar create failed (exit {result.returncode}): {result.stderr.strip()}")
        if on_progress:
            on_progress(len(files), len(files))
    finally:
        os.remove(listfile)


def verify(exe_path: str, archive_path: str) -> bool:
    result = subprocess.run(
        [exe_path, "t", archive_path], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return result.returncode == 0
