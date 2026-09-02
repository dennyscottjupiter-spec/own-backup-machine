# ---
# purpose: write the @listfile each archiver reads, one path per line, in ITS OWN encoding
# exports: write_sevenzip_listfile(), write_winrar_listfile()
# gotcha: 7-Zip wants UTF-8 (with -scsUTF-8), WinRAR wants UTF-16LE WITH a BOM — swap them and
#         every accented path silently vanishes from the archive
# ---
from __future__ import annotations

import os
import tempfile


def write_sevenzip_listfile(files: list[str]) -> str:
    fd, path = tempfile.mkstemp(prefix="obm_7z_list_", suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        for p in files:
            f.write(p + "\n")
    return path


def write_winrar_listfile(files: list[str]) -> str:
    fd, path = tempfile.mkstemp(prefix="obm_rar_list_", suffix=".txt")
    with os.fdopen(fd, "wb") as f:
        f.write(b"\xff\xfe")  # UTF-16LE BOM
        for p in files:
            f.write((p + "\r\n").encode("utf-16-le"))
    return path
