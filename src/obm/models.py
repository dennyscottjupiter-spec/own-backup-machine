# ---
# purpose: the records that flow through the whole pipeline, mutated in place
# exports: CandidateFile, ScanIssue, VolumePlan, DryRunResult, RunRecord
# gotcha: CandidateFile uses slots=True — do not add fields without checking RAM impact
# ---
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CandidateFile:
    path: str
    volume: str
    size: int
    mtime_ns: int
    attributes: int
    source: str  # "usn" | "walk" | "carryover"
    reason: int = 0  # USN reason mask; 0 from walk

    verdict: str = "keep"  # "keep" | "drop"
    drop_rule: str = ""
    tags: frozenset[str] = field(default_factory=frozenset)
    selected: bool = True
    content_hash: str = ""


@dataclass(slots=True)
class ScanIssue:
    path: str
    kind: str  # denied|locked|vanished|toolong|reparse|journal_reset|unreadable
    detail: str = ""
    size: int = 0  # 0 when the size could not be read -- these sort last


@dataclass(slots=True)
class VolumePlan:
    letter: str
    guid_path: str
    fs_name: str
    method: str  # "usn" | "walk"
    fallback_reason: str
    cursor: int
    walk_cutoff_ns: int
    roots: list[str]


@dataclass(slots=True)
class DryRunResult:
    candidates: list[CandidateFile]
    issues: list[ScanIssue]
    plans: list[VolumePlan]


@dataclass(slots=True)
class RunRecord:
    run_id: str
    started_utc: str
    finished_utc: str
    status: str  # "ok" | "failed" | "partial"
    archive_path: str
    file_count: int
    total_bytes: int
    issue_count: int
