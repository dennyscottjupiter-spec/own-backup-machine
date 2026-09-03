# ---
# purpose: human-readable labels, counts, size resolution, root-folder grouping and a paste-ready
#          report for ScanIssue
# exports: KIND_LABELS, IssueGroup, label(), summarize(), by_size(), resolve_sizes(),
#          size_prefix(), report(), group_by_root(), relative_to()
# depends: models.ScanIssue, humanize.py, winapi/longpath.py
# gotcha: resolve_sizes() stats the filesystem, so it runs in the scan worker (dryrun), never on
#         the Tk thread; it is capped because a bad volume can produce issues by the hundred-thousand
# ---
from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass

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

# how many leading path components decide "these issues live in the same place". Four covers
# C:\Users\<name>\AppData -- one collapsed row instead of a screenful of its subfolders.
GROUP_DEPTH = 4


@dataclass(slots=True)
class IssueGroup:
    root: str
    issues: list[ScanIssue]
    total_size: int


def label(issue: ScanIssue) -> str:
    return KIND_LABELS.get(issue.kind, issue.kind)


def summarize(issues: list[ScanIssue]) -> dict[str, int]:
    return dict(Counter(i.kind for i in issues))


def by_size(issues: list[ScanIssue]) -> list[ScanIssue]:
    """Biggest offender first — what the UI list and the copied report are both ordered by."""
    return sorted(issues, key=lambda i: -i.size)


def _components(path: str) -> list[str]:
    return path.replace("/", "\\").split("\\")


def _folder_of(path: str) -> list[str]:
    return _components(os.path.dirname(path))


def _common_folder(issues: list[ScanIssue]) -> str:
    """The deepest folder every issue in the bucket actually shares -- so a bucket that is really
    all one Temp folder is labelled with that folder, not with its four-component key."""
    common = _folder_of(issues[0].path)
    for issue in issues[1:]:
        parts = _folder_of(issue.path)
        n = 0
        while n < len(common) and n < len(parts) and common[n].lower() == parts[n].lower():
            n += 1
        common = common[:n]
    return "\\".join(common)


def group_by_root(issues: list[ScanIssue], depth: int = GROUP_DEPTH) -> list[IssueGroup]:
    """Collapse issues that share a root folder into one group, biggest group first."""
    buckets: dict[str, list[ScanIssue]] = {}
    for issue in issues:
        key = "\\".join(_folder_of(issue.path)[:depth]).lower()
        buckets.setdefault(key, []).append(issue)

    groups = [
        IssueGroup(root=_common_folder(bucket), issues=by_size(bucket), total_size=sum(i.size for i in bucket))
        for bucket in buckets.values()
    ]
    groups.sort(key=lambda g: (-g.total_size, -len(g.issues), g.root))
    return groups


def relative_to(root: str, path: str) -> str:
    """The part of `path` below `root` -- what a collapsed group's child rows show."""
    prefix = root.rstrip("\\") + "\\"
    return path[len(prefix):] if path.lower().startswith(prefix.lower()) else path


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
