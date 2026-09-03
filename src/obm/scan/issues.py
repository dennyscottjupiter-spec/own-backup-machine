# ---
# purpose: human-readable labels, counts, size resolution and a paste-ready report for ScanIssue
# exports: KIND_LABELS, label(), summarize(), by_size(), resolve_sizes(), size_prefix(), report()
# depends: models.ScanIssue, humanize.py, winapi/longpath.py
# gotcha: resolve_sizes() stats the filesystem, so it runs in the scan worker (dryrun), never on
#         the Tk thread; it is capped because a bad volume can produce issues by the hundred-thousand
# ---
from __future__ import annotations

import os
from collections import Counter

from .. import humanize
from ..models import ScanIssue
from ..winapi.longpath import to_extended

KIND_LABELS = {
    "denied": "Access denied",
    "locked": "Locked by another process",
    "vanished": "Vanished during scan",
    "toolong": "Path too long",
    "reparse": "Junction or symlink skipped",
    "journal_reset": "USN journal reset — re-baselined",
    "unreadable": "Directory unreadable",
}

MAX_SIZE_LOOKUPS = 5000
UNKNOWN_SIZE = "?"


def label(issue: ScanIssue) -> str:
    return KIND_LABELS.get(issue.kind, issue.kind)


def summarize(issues: list[ScanIssue]) -> dict[str, int]:
    return dict(Counter(i.kind for i in issues))


def by_size(issues: list[ScanIssue]) -> list[ScanIssue]:
    """Biggest offender first — what the UI list and the copied report are both ordered by."""
    return sorted(issues, key=lambda i: -i.size)


def resolve_sizes(issues: list[ScanIssue], limit: int = MAX_SIZE_LOOKUPS) -> None:
    """Fill in the size of every issue path we can still stat. A locked or denied file still
    reports its size; a vanished one does not, and keeps size 0."""
    for issue in issues[:limit]:
        if issue.size:
            continue
        try:
            issue.size = os.stat(to_extended(issue.path)).st_size
        except OSError:
            pass


def size_prefix(issue: ScanIssue) -> str:
    return humanize.size(issue.size) if issue.size else UNKNOWN_SIZE


def report(issues: list[ScanIssue]) -> str:
    """Plain text of every issue — what the UI's Copy button puts on the clipboard."""
    if not issues:
        return "No issues."

    counts = summarize(issues)
    header = ", ".join(
        f"{KIND_LABELS.get(kind, kind)}: {n}" for kind, n in sorted(counts.items(), key=lambda kv: -kv[1])
    )
    lines = [f"{len(issues)} scan issues — {header}", ""]
    for issue in by_size(issues):
        detail = f" — {issue.detail}" if issue.detail else ""
        lines.append(f"[{size_prefix(issue)}] [{label(issue)}] {issue.path}{detail}")
    return "\n".join(lines)
