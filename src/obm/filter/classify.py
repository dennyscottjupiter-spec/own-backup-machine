# ---
# purpose: attributes + size -> display tags/category; the OneDrive placeholder trap lives here
# exports: classify_tags(), category_of()
# depends: rules.py, winapi/constants.py
# gotcha: PINNED is NOT a placeholder flag — it means locally present, must not gate on it
# ---
from __future__ import annotations

import os

from ..winapi.constants import CLOUD_PLACEHOLDER_MASK
from .rules import CATEGORIES

_EXT_TO_CATEGORY = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}


def is_placeholder(attributes: int) -> bool:
    return bool(attributes & CLOUD_PLACEHOLDER_MASK)


def classify_tags(attributes: int, size: int, big_file_mb: int, existing: frozenset[str] = frozenset()) -> frozenset[str]:
    tags = set(existing)
    if is_placeholder(attributes):
        tags.add("placeholder")
    if size >= big_file_mb * 1024 * 1024:
        tags.add("big")
    return frozenset(tags)


def category_of(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return _EXT_TO_CATEGORY.get(ext, "unknown")
