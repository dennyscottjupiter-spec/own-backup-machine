# ---
# purpose: scan, archive, and commit state as ONE unit -- only on a verified success
# exports: run(), run_cli()
# depends: pipeline/dryrun.py, archive/{detect,naming,writer,manifest}, state/{cursors,store,fingerprints,carryover,history}
# gotcha: a locked/denied file is caught by a pre-flight open, not by parsing 7z/rar stderr --
#         that is what makes carryover backend-agnostic
# ---
from __future__ import annotations

import ctypes
import time
from datetime import datetime, timezone

from .. import config as config_mod
from .. import humanize
from ..archive import detect, manifest, naming, writer
from ..models import CandidateFile, RunRecord
from ..state import carryover
from ..state import cursors as cursors_mod
from ..state import history
from ..state import store as state_store
from ..state.fingerprints import Fingerprints
from ..winapi import constants as wc
from ..winapi import kernel32 as k32
from ..winapi.longpath import to_extended
from . import dryrun


def _probe_open(path: str) -> str | None:
    """None if openable right now, else the carryover reason: 'locked' or 'denied'.

    Uses CreateFileW directly (not Python's open()) because msvcrt's runtime
    collapses every Win32 open failure to errno 13 with no winerror, which
    would make ERROR_SHARING_VIOLATION and ERROR_ACCESS_DENIED indistinguishable.
    """
    handle = k32.CreateFileW(
        to_extended(path),
        wc.GENERIC_READ,
        wc.FILE_SHARE_READ | wc.FILE_SHARE_WRITE | wc.FILE_SHARE_DELETE,
        None,
        wc.OPEN_EXISTING,
        0,
        None,
    )
    if not k32.is_invalid_handle(handle):
        k32.CloseHandle(handle)
        return None

    err = ctypes.get_last_error()
    return "locked" if err in (wc.ERROR_SHARING_VIOLATION, wc.ERROR_LOCK_VIOLATION) else "denied"


def _preflight(candidates: list[CandidateFile]) -> tuple[list[CandidateFile], list[carryover.CarryEntry]]:
    ready: list[CandidateFile] = []
    carried: list[carryover.CarryEntry] = []
    for c in candidates:
        reason = _probe_open(c.path)
        if reason is None:
            ready.append(c)
        else:
            carried.append(carryover.CarryEntry(path=c.path, reason=reason))
    return ready, carried


def run(cfg: config_mod.Config) -> RunRecord:
    run_started = datetime.now(timezone.utc)
    run_id = naming.run_id_for(run_started)

    result = dryrun.run(cfg)
    kept = [c for c in result.candidates if c.verdict == "keep" and c.selected]
    to_archive, newly_carried = _preflight(kept)

    tool = detect.detect()
    writer.cleanup_stale_parts(cfg.destination_path)
    archive_filename = naming.archive_name(tool.name, run_started)

    final_path = writer.write_archive(
        tool, cfg.archive_level, [c.path for c in to_archive], cfg.destination_path, archive_filename
    )

    finished = datetime.now(timezone.utc)
    record = RunRecord(
        run_id=run_id,
        started_utc=run_started.isoformat(),
        finished_utc=finished.isoformat(),
        status="ok",
        archive_path=final_path,
        file_count=len(to_archive),
        total_bytes=sum(c.size for c in to_archive),
        issue_count=len(result.issues) + len(newly_carried),
    )

    manifest.write(final_path + ".manifest.json", manifest.build(record, to_archive, result.issues))

    # Commit cursors + fingerprints + history + carryover as one unit, only now that
    # the archive is verified and renamed into place.
    app_state = state_store.load()
    now_iso = cursors_mod.now_iso()
    for plan in result.plans:
        cursors_mod.mark_run(app_state, plan.guid_path, plan.letter, now_iso)
    state_store.save(app_state)

    with Fingerprints() as fp:
        for c in to_archive:
            fp.upsert(c.path, c.size, c.mtime_ns, c.content_hash, run_id)

    carryover.save(newly_carried)
    history.append(record)
    return record


def run_cli() -> int:
    cfg = config_mod.load()
    if not cfg.destination_path:
        print("No destination configured. Edit config.toml and set [destination] path.")
        return 1

    started = time.time()
    record = run(cfg)
    elapsed = time.time() - started

    print(f"archived {record.file_count} files ({humanize.size(record.total_bytes)}) in {humanize.duration(elapsed)}")
    print(f"-> {record.archive_path}")
    if record.issue_count:
        print(f"issues / carried over: {record.issue_count}")
    return 0
