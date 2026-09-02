# ---
# purpose: drop unchanged-fingerprint false positives before the blocklist even runs
# exports: confirm()
# depends: state/fingerprints.py, filter/classify.py, hashing.py
# gotcha: never hashes a placeholder or a file over hash_max_mb — trust mtime, keep it
# ---
from __future__ import annotations

from ..filter.classify import is_placeholder
from ..models import CandidateFile
from ..state.fingerprints import Fingerprints
from .hashing import hash_file


def confirm(candidate: CandidateFile, fp: Fingerprints, hash_max_mb: int) -> bool:
    """True = real change, keep for scoring. False = unchanged fingerprint, drop."""
    row = fp.lookup(candidate.path)
    if row is None:
        return True

    stored_size, stored_mtime_ns, stored_hash = row
    if candidate.size == stored_size and candidate.mtime_ns == stored_mtime_ns:
        return False
    if candidate.size != stored_size:
        return True

    # size matches, mtime differs -> ambiguous (e.g. a touch-save with identical content)
    if is_placeholder(candidate.attributes) or candidate.size > hash_max_mb * 1024 * 1024:
        return True

    new_hash = hash_file(candidate.path)
    candidate.content_hash = new_hash
    return new_hash != stored_hash
