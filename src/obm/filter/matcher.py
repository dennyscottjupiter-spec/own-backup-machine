# ---
# purpose: decide keep/drop for one path against the blocklist, independent of walk order
# exports: match()
# depends: rules.py
# gotcha: checks EVERY ancestor dir name, not just the leaf — USN candidates skip no directory walk
# ---
from __future__ import annotations

import os
import re

from .rules import BLOCKED_DIR_NAMES, BLOCKED_EXTENSIONS, BLOCKED_FILE_NAMES, BLOCKED_PATH_PATTERNS

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATH_PATTERNS]


def match(path: str, extra_excludes: list[str] | None = None) -> tuple[bool, str]:
    parts = path.replace("/", "\\").split("\\")
    for part in parts[:-1]:
        if part.lower() in BLOCKED_DIR_NAMES:
            return False, f"blocked-dir:{part.lower()}"

    name = parts[-1]
    if name.lower() in BLOCKED_FILE_NAMES:
        return False, f"blocked-file:{name.lower()}"

    ext = os.path.splitext(name)[1].lower()
    if ext in BLOCKED_EXTENSIONS:
        return False, f"blocked-ext:{ext}"

    lower_path = path.lower()
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(lower_path):
            return False, f"blocked-pattern:{pattern.pattern}"

    for exclude in extra_excludes or ():
        norm = exclude.lower().rstrip("\\")
        if lower_path == norm or lower_path.startswith(norm + "\\"):
            return False, "user-exclude"

    return True, ""
