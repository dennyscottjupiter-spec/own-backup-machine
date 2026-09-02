# ---
# purpose: extended-length (\\?\) path helpers, UNC-aware
# exports: to_extended(), to_display()
# gotcha: normalize BEFORE prefixing — \\?\ disables ".." resolution
# ---
from __future__ import annotations

import os

_EXTENDED_PREFIX = "\\\\?\\"
_EXTENDED_UNC_PREFIX = "\\\\?\\UNC\\"


def to_extended(path: str) -> str:
    if path.startswith(_EXTENDED_PREFIX):
        return path
    normalized = os.path.normpath(path)
    if normalized.startswith("\\\\"):
        return _EXTENDED_UNC_PREFIX + normalized.lstrip("\\")
    return _EXTENDED_PREFIX + normalized


def to_display(path: str) -> str:
    if path.startswith(_EXTENDED_UNC_PREFIX):
        return "\\\\" + path[len(_EXTENDED_UNC_PREFIX):]
    if path.startswith(_EXTENDED_PREFIX):
        return path[len(_EXTENDED_PREFIX):]
    return path
