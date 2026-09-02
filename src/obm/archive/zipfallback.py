# ---
# purpose: stdlib zipfile backend — always available, same signature as sevenzip.py/winrar.py
# exports: create(), verify()
# depends: naming.arcname_for, winapi/longpath.py
# gotcha: opens files through to_extended() for long-path safety; exe_path is unused (no external tool)
# ---
from __future__ import annotations

import zipfile
from typing import Callable

from ..winapi.longpath import to_extended
from .naming import arcname_for


def create(
    exe_path: str,
    level: int,
    out_path: str,
    files: list[str],
    on_progress: Callable[[int, int], None] | None = None,
) -> None:
    compression = zipfile.ZIP_STORED if level <= 0 else zipfile.ZIP_DEFLATED
    total = len(files)
    with zipfile.ZipFile(out_path, "w", compression=compression) as zf:
        for i, path in enumerate(files, 1):
            zf.write(to_extended(path), arcname=arcname_for(path))
            if on_progress:
                on_progress(i, total)


def verify(exe_path: str, archive_path: str) -> bool:
    with zipfile.ZipFile(archive_path) as zf:
        return zf.testzip() is None
