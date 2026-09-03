"""The regression guard for the delta baseline.

A run archives only the files the user actually selected. Everything else -- deselected,
filtered, locked -- must still be offered by the NEXT scan. Anything that keys "already
handled" off the clock instead of off the archived-fingerprint index silently loses those
files forever, which is the worst possible failure for a backup tool.
"""
from __future__ import annotations

import os

from obm.config import Config
from obm.pipeline import dryrun
from obm.scan import plan as plan_mod
from obm.state import cursors
from obm.state import store as state_store
from obm.state.fingerprints import Fingerprints
from obm.winapi.volumes import VolumeInfo

VOLUME = VolumeInfo(letter="C:", drive_type=3, fs_name="NTFS", usn_capable=False,
                    guid_path="\\\\?\\Volume{test}\\")


def _isolate(monkeypatch, tmp_path, root):
    """Real build_plan(), real walk -- only the volume list, its roots and the data dir are faked,
    so the run-to-run planning that caused the regression is genuinely under test."""
    # pytest's tmp_path lives under AppData\Local\Temp, which the blocklist drops wholesale.
    # This test is about the delta baseline, not the blocklist.
    monkeypatch.setattr("obm.filter.matcher._COMPILED_PATTERNS", [])

    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr("obm.paths.data_dir", lambda: data)
    monkeypatch.setattr("obm.paths.ensure_data_dir", lambda: data)

    monkeypatch.setattr(dryrun.volumes, "list_volumes", lambda: [VOLUME])
    monkeypatch.setattr(plan_mod.roots, "volume_roots", lambda cfg, vols: {"C:": [str(root)]})


def _kept_names(result):
    return {os.path.basename(c.path) for c in result.candidates if c.verdict == "keep"}


def _fingerprint(result, *basenames):
    """What execute.run() commits: a fingerprint for the files that really went in."""
    with Fingerprints() as fp:
        for c in result.candidates:
            if os.path.basename(c.path) in basenames:
                fp.upsert(c.path, c.size, c.mtime_ns, c.content_hash, "run-1")


def test_an_old_file_survives_a_completed_run_that_skipped_it(monkeypatch, tmp_path):
    root = tmp_path / "files"
    root.mkdir()
    (root / "archived.txt").write_text("in the archive")
    (root / "deselected.txt").write_text("user unticked this one")

    _isolate(monkeypatch, tmp_path, root)
    cfg = Config()

    first = dryrun.run(cfg)
    assert _kept_names(first) == {"archived.txt", "deselected.txt"}

    _fingerprint(first, "archived.txt")
    state = state_store.load()
    cursors.mark_run(state, VOLUME.guid_path, VOLUME.letter, cursors.now_iso())
    state_store.save(state)

    second = dryrun.run(cfg)
    assert "deselected.txt" in _kept_names(second), "a skipped file must be offered again"


def test_an_archived_file_is_dropped_by_its_fingerprint_not_by_the_clock(monkeypatch, tmp_path):
    root = tmp_path / "files"
    root.mkdir()
    target = root / "archived.txt"
    target.write_text("in the archive")

    _isolate(monkeypatch, tmp_path, root)
    cfg = Config()

    _fingerprint(dryrun.run(cfg), "archived.txt")

    second = dryrun.run(cfg)
    dropped = {os.path.basename(c.path): c.drop_rule for c in second.candidates if c.verdict == "drop"}
    assert dropped == {"archived.txt": "unchanged-fingerprint"}

    target.write_text("edited after the run, different length")
    assert _kept_names(dryrun.run(cfg)) == {"archived.txt"}
