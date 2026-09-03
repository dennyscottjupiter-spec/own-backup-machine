# ---
# purpose: sidecar JSON describing an archive's contents — the history panel never opens the archive
# exports: MANIFEST_SUFFIX, build(), write(), read()
# depends: models.py
# ---
from __future__ import annotations

import json

from ..models import CandidateFile, RunRecord, ScanIssue

MANIFEST_SUFFIX = ".manifest.json"


def build(run: RunRecord, files: list[CandidateFile], issues: list[ScanIssue]) -> dict:
    return {
        "run_id": run.run_id,
        "started_utc": run.started_utc,
        "finished_utc": run.finished_utc,
        "status": run.status,
        "archive_path": run.archive_path,
        "file_count": run.file_count,
        "total_bytes": run.total_bytes,
        "files": [{"path": f.path, "size": f.size, "mtime_ns": f.mtime_ns} for f in files],
        "issues": [{"path": i.path, "kind": i.kind, "detail": i.detail} for i in issues],
    }


def write(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def read(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
