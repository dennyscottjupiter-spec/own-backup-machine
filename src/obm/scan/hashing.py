# ---
# purpose: content hashing used only to disambiguate a same-size, different-mtime file
# exports: hash_file()
# depends: winapi/longpath.py
# ---
from __future__ import annotations

import hashlib

from ..winapi.longpath import to_extended

CHUNK_SIZE = 1024 * 1024


def hash_file(path: str) -> str:
    h = hashlib.blake2b()
    with open(to_extended(path), "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()
