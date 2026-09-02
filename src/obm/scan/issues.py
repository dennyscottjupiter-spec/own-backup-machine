# ---
# purpose: human-readable labels, counts and a paste-ready report for ScanIssue
# exports: KIND_LABELS, label(), summarize(), report()
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


def report(issues: list[ScanIssue]) -> str:
    """Plain text of every issue — what the UI's Copy button puts on the clipboard."""
    if not issues:
        return "No issues."

    counts = summarize(issues)
    header = ", ".join(
        f"{KIND_LABELS.get(kind, kind)}: {n}" for kind, n in sorted(counts.items(), key=lambda kv: -kv[1])
    )
    lines = [f"{len(issues)} scan issues — {header}", ""]
    for issue in issues:
        detail = f" — {issue.detail}" if issue.detail else ""
        lines.append(f"[{label(issue)}] {issue.path}{detail}")
    return "\n".join(lines)
