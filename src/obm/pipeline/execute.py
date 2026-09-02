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
from typing import Callable

from .. import config as config_mod
from .. import humanize
from ..archive import detect, manifest, naming, writer
from ..models import CandidateFile, DryRunResult, RunRecord
from ..scan import usn_journal
from ..state import carryover
from ..state import cursors as cursors_mod
from ..state import history
from ..state import store as state_store
from ..state.fingerprints import Fingerprints
from ..winapi import constants as wc
from ..winapi import kernel32 as k32
from ..winapi.longpath import to_extended
from . import dryrun, selection


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


def _snapshot_journal(letter: str) -> tuple[int, int]:
    """Current (journal_id, next_usn) for a volume, or (0, 0) if it has no usable journal --
    that's harmless since build_plan() only consults these fields for usn_capable volumes."""
    try:
        handle = usn_journal.open_volume(letter)
    except OSError:
        return 0, 0
    try:
        info = usn_journal.query_journal(handle)
    except OSError:
        return 0, 0
    finally:
        k32.CloseHandle(handle)
    return info.journal_id, info.next_usn


def run(
    cfg: config_mod.Config,
    result: DryRunResult | None = None,
    on_progress: Callable[[int, int], None] | None = None,
    on_stage: Callable[[str], None] | None = None,
) -> RunRecord:
    """`result` lets a caller (the UI) pass its already-scanned, checkbox-edited DryRunResult
    instead of triggering a second, independent scan that would silently discard any
    unticked big files -- the CLI path leaves it None and scans fresh."""
    run_started = datetime.now(timezone.utc)
    run_id = naming.run_id_for(run_started)

    def say(text: str) -> None:
        if on_stage:
            on_stage(text)

    if result is None:
        say("Scanning for changed files")
        result = dryrun.run(cfg)
    kept = selection.selected_files(result.candidates)

    say(f"Checking {humanize.count(len(kept))} files for locks")
    to_archive, newly_carried = _preflight(kept)
    if newly_carried:
        say(f"{humanize.count(len(newly_carried))} locked or denied — carried over to the next run")

    tool = detect.detect()
    say(f"Using {tool.name} at compression level {cfg.archive_level}")
    writer.cleanup_stale_parts(cfg.destination_path)
    archive_filename = naming.archive_name(tool.name, run_started)

    final_path = writer.write_archive(
        tool,
        cfg.archive_level,
        [c.path for c in to_archive],
        cfg.destination_path,
        archive_filename,
        on_progress,
        on_stage,
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

    say("Writing the manifest")
    manifest.write(final_path + ".manifest.json", manifest.build(record, to_archive, result.issues))

    # Commit cursors + fingerprints + history + carryover as one unit, only now that
    # the archive is verified and renamed into place. Every completed run -- walk or usn --
    # re-baselines the journal snapshot so a future usn-enabled run has a fresh, valid cursor
    # to resume from, per the cursor-validation ladder in state/cursors.py.
    say("Committing cursors, fingerprints, history and carryover")
    app_state = state_store.load()
    now_iso = cursors_mod.now_iso()
    for plan in result.plans:
        journal_id, next_usn = _snapshot_journal(plan.letter)
        cursors_mod.mark_run(app_state, plan.guid_path, plan.letter, now_iso, journal_id, next_usn)
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

    print(
        f"archived {humanize.count(record.file_count)} files "
        f"({humanize.size(record.total_bytes)}) in {humanize.duration(elapsed)}"
    )
    print(f"-> {record.archive_path}")
    if record.issue_count:
        print(f"issues / carried over: {humanize.count(record.issue_count)}")
    return 0
