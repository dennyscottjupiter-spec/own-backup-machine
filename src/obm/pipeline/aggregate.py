# ---
# purpose: read-only summary view over a scored candidate list — feeds CLI, panels, charts
# exports: Summary, build_summary()
# depends: models.py, filter/classify.py, scan/issues.py
# gotcha: placeholders are counted separately and never added to kept bytes — never archived
# ---
from __future__ import annotations

from dataclasses import dataclass, field

from ..filter.classify import category_of
from ..models import CandidateFile, ScanIssue
from ..scan.issues import summarize as summarize_issues


@dataclass(slots=True)
class Summary:
    kept_count: int = 0
    kept_bytes: int = 0
    dropped_count: int = 0
    dropped_bytes: int = 0
    placeholder_count: int = 0
    by_category: dict[str, tuple[int, int]] = field(default_factory=dict)
    by_volume: dict[str, tuple[int, int]] = field(default_factory=dict)
    big_files: list[CandidateFile] = field(default_factory=list)
    issue_counts: dict[str, int] = field(default_factory=dict)


def _bump(table: dict[str, tuple[int, int]], key: str, size: int) -> None:
    count, total = table.get(key, (0, 0))
    table[key] = (count + 1, total + size)


def build_summary(candidates: list[CandidateFile], issues: list[ScanIssue]) -> Summary:
    s = Summary()
    for c in candidates:
        if c.verdict == "drop":
            s.dropped_count += 1
            s.dropped_bytes += c.size
            continue
        if "placeholder" in c.tags:
            s.placeholder_count += 1
            continue
        s.kept_count += 1
        s.kept_bytes += c.size
        _bump(s.by_category, category_of(c.path), c.size)
        _bump(s.by_volume, c.volume, c.size)
        if "big" in c.tags:
            s.big_files.append(c)

    s.big_files.sort(key=lambda c: c.size, reverse=True)
    s.issue_counts = summarize_issues(issues)
    return s
