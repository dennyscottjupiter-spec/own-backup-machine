# ---
# purpose: the final file list for archiving -- kept verdict AND still checked in the UI
# exports: selected_files()
# depends: models.CandidateFile
# ---
from __future__ import annotations

from ..models import CandidateFile


def selected_files(candidates: list[CandidateFile]) -> list[CandidateFile]:
    return [c for c in candidates if c.verdict == "keep" and c.selected]
