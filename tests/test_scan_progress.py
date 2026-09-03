"""The scan has to be legible while it runs: a live count, a folder, and an honest percentage."""
from __future__ import annotations

from obm.config import Config
from obm.pipeline import dryrun
from obm.scan import plan as plan_mod
from obm.state import store as state_store
from obm.ui.scan_banner import _short_path
from obm.winapi.volumes import VolumeInfo

VOLUME = VolumeInfo(letter="C:", drive_type=3, fs_name="NTFS", usn_capable=False,
                    guid_path="\\\\?\\Volume{test}\\")


def _isolate(monkeypatch, tmp_path, root):
    monkeypatch.setattr("obm.filter.matcher._COMPILED_PATTERNS", [])
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr("obm.paths.data_dir", lambda: data)
    monkeypatch.setattr("obm.paths.ensure_data_dir", lambda: data)
    monkeypatch.setattr(dryrun.volumes, "list_volumes", lambda: [VOLUME])
    monkeypatch.setattr(plan_mod.roots, "volume_roots", lambda cfg, vols: {"C:": [str(root)]})


def test_a_long_path_is_shortened_to_its_last_few_folders():
    assert _short_path("C:\\Users\\me\\Pictures\\2026\\trip\\a.jpg") == "...\\Pictures\\2026\\trip"


def test_a_short_path_is_left_alone():
    assert _short_path("C:\\Users\\a.jpg") == "C:\\Users"


def test_the_scan_reports_progress_and_remembers_its_total(monkeypatch, tmp_path):
    root = tmp_path / "files"
    root.mkdir()
    for i in range(5):
        (root / f"f{i}.txt").write_text("x")

    _isolate(monkeypatch, tmp_path, root)
    monkeypatch.setattr(dryrun, "SCAN_TICK", 2)

    ticks = []
    dryrun.run(Config(), on_scan=lambda seen, expected, path: ticks.append((seen, expected, path)))

    assert [seen for seen, _, _ in ticks] == [2, 4]
    assert all(expected == 0 for _, expected, _ in ticks), "the first scan has nothing to divide by"
    assert all(p.startswith(str(root)) for _, _, p in ticks)
    assert state_store.load().last_scan_files == 5


def test_the_next_scan_gets_the_previous_total_to_measure_against(monkeypatch, tmp_path):
    root = tmp_path / "files"
    root.mkdir()
    for i in range(4):
        (root / f"f{i}.txt").write_text("x")

    _isolate(monkeypatch, tmp_path, root)
    monkeypatch.setattr(dryrun, "SCAN_TICK", 2)

    dryrun.run(Config())
    ticks = []
    dryrun.run(Config(), on_scan=lambda seen, expected, path: ticks.append((seen, expected)))

    assert ticks == [(2, 4), (4, 4)]
