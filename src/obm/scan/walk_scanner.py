# ---
# purpose: iterative scandir walk, mtime cutoff, reparse-point skip — the reference scanner
# exports: scan(), make_candidate()
# depends: models.py, filter/rules.py, winapi/{constants,longpath}.py
# gotcha: a denied directory never truncates its parent; reparse points are skipped AND reported
# ---
from __future__ import annotations

import os
from collections import deque
from typing import Iterator

from ..filter.rules import BLOCKED_DIR_NAMES
from ..models import CandidateFile, ScanIssue, VolumePlan
from ..winapi.constants import FILE_ATTRIBUTE_REPARSE_POINT
from ..winapi.longpath import to_display, to_extended

MAX_DEPTH = 64


def make_candidate(path: str, st: os.stat_result, source: str) -> CandidateFile:
    drive = os.path.splitdrive(path)[0].upper()
    return CandidateFile(
        path=path,
        volume=drive,
        size=st.st_size,
        mtime_ns=st.st_mtime_ns,
        attributes=st.st_file_attributes,
        source=source,
    )


def scan(plan: VolumePlan) -> Iterator[CandidateFile | ScanIssue]:
    stack = deque(plan.roots)
    depth = {r: 0 for r in plan.roots}

    while stack:
        current = stack.pop()
        if depth[current] > MAX_DEPTH:
            yield ScanIssue(to_display(current), "reparse", "depth cap")
            continue
        try:
            entries = list(os.scandir(to_extended(current)))
        except PermissionError:
            yield ScanIssue(to_display(current), "denied", "")
            continue
        except OSError as e:
            yield ScanIssue(to_display(current), "unreadable", str(e.winerror))
            continue

        for e in entries:
            display_path = to_display(e.path)
            try:
                st = e.stat(follow_symlinks=False)
                if st.st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT:
                    yield ScanIssue(display_path, "reparse", "junction/symlink skipped")
                    continue
                if e.is_dir(follow_symlinks=False):
                    if e.name.lower() in BLOCKED_DIR_NAMES:
                        continue
                    stack.append(e.path)
                    depth[e.path] = depth[current] + 1
                elif st.st_mtime_ns >= plan.walk_cutoff_ns:
                    yield make_candidate(display_path, st, source="walk")
            except OSError:
                yield ScanIssue(display_path, "vanished", "")
