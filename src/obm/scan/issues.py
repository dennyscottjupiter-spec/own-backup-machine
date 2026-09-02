# ---
# purpose: human-readable labels and counts for ScanIssue — a first-class pipeline output
# exports: KIND_LABELS, label(), summarize()
# depends: models.ScanIssue
# ---
from __future__ import annotations

from collections import Counter

from ..models import ScanIssue

KIND_LABELS = {
    "denied": "Access denied",
    "locked": "Locked by another process",
    "vanished": "Vanished during scan",
    "toolong": "Path too long",
    "reparse": "Junction or symlink skipped",
    "journal_reset": "USN journal reset — re-baselined",
    "unreadable": "Directory unreadable",
}


def label(issue: ScanIssue) -> str:
    return KIND_LABELS.get(issue.kind, issue.kind)


def summarize(issues: list[ScanIssue]) -> dict[str, int]:
    return dict(Counter(i.kind for i in issues))
