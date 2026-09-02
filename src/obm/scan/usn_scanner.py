# ---
# purpose: USN change events -> deduped CandidateFile, via fileid resolution + a fresh os.stat
# exports: scan()
# depends: usn_journal.py, usn_records.py, winapi/{fileid,longpath,constants}
# gotcha: dedupes by resolved path -- one file can generate several USN records in a session;
#         a parent that fails to open (since-deleted directory) -> ScanIssue(kind="vanished")
# ---
from __future__ import annotations

import os
from typing import Iterator

from ..models import CandidateFile, ScanIssue, VolumePlan
from ..winapi import constants as wc
from ..winapi import kernel32 as k32
from ..winapi.fileid import FileIdResolver
from ..winapi.longpath import to_display, to_extended
from . import usn_journal, usn_records
from .walk_scanner import make_candidate


def _under_any_root(path: str, roots: list[str]) -> bool:
    lower = path.lower()
    return any(lower.startswith(root.lower()) for root in roots)


def scan(plan: VolumePlan) -> Iterator[CandidateFile | ScanIssue]:
    handle = usn_journal.open_volume(plan.letter)
    try:
        info = usn_journal.query_journal(handle)
        resolver = FileIdResolver(handle)
        seen: set[str] = set()

        for raw in usn_journal.read_buffers(handle, info.journal_id, plan.cursor):
            for record in usn_records.parse_records(raw):
                if record.file_attributes & wc.FILE_ATTRIBUTE_DIRECTORY:
                    continue  # only files are archived

                path = resolver.resolve(record.file_reference_number)
                if path is None:
                    yield ScanIssue(f"<frn {record.file_reference_number}>", "vanished", "parent open failed")
                    continue

                display = to_display(path)
                key = display.lower()
                if key in seen:
                    continue
                seen.add(key)

                if not _under_any_root(display, plan.roots):
                    continue

                try:
                    st = os.stat(to_extended(display))
                except OSError:
                    yield ScanIssue(display, "vanished", "")
                    continue

                yield make_candidate(display, st, source="usn")
    finally:
        k32.CloseHandle(handle)
