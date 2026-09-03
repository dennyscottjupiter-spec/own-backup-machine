import os
import time

from obm.models import CandidateFile, ScanIssue, VolumePlan
from obm.scan import walk_scanner
from obm.winapi.constants import FILE_ATTRIBUTE_REPARSE_POINT
from obm.winapi.longpath import to_extended


def _plan(root):
    return VolumePlan(letter="C:", guid_path="", fs_name="NTFS", method="walk",
                       fallback_reason="test", cursor=0, roots=[str(root)])


def test_age_never_hides_a_file(tmp_path):
    """The walk yields EVERY file. Only the archived-fingerprint index may drop one."""
    ancient = tmp_path / "ancient.txt"
    fresh = tmp_path / "fresh.txt"
    ancient.write_text("old")
    fresh.write_text("new")

    decade_ago = time.time_ns() - 10 * 365 * 24 * 3600 * 1_000_000_000
    os.utime(ancient, ns=(decade_ago, decade_ago))

    candidates = [i for i in walk_scanner.scan(_plan(tmp_path)) if isinstance(i, CandidateFile)]
    assert {os.path.basename(c.path) for c in candidates} == {"ancient.txt", "fresh.txt"}


def test_denied_subdirectory_reported_and_scan_continues(tmp_path, monkeypatch):
    denied_dir = tmp_path / "denied"
    denied_dir.mkdir()
    (tmp_path / "ok.txt").write_text("data")

    real_scandir = os.scandir
    denied_extended = to_extended(str(denied_dir))

    def fake_scandir(path):
        if path == denied_extended:
            raise PermissionError("simulated denial")
        return real_scandir(path)

    monkeypatch.setattr(walk_scanner.os, "scandir", fake_scandir)

    plan = _plan(tmp_path)
    items = list(walk_scanner.scan(plan))
    issues = [i for i in items if isinstance(i, ScanIssue)]
    candidates = [i for i in items if isinstance(i, CandidateFile)]

    assert any(i.kind == "denied" for i in issues)
    assert any(os.path.basename(c.path) == "ok.txt" for c in candidates)


class _FakeStat:
    def __init__(self, attributes):
        self.st_file_attributes = attributes
        self.st_size = 0
        self.st_mtime_ns = 0


class _FakeEntry:
    def __init__(self, path, name, is_dir, attributes):
        self.path = path
        self.name = name
        self._is_dir = is_dir
        self._attributes = attributes

    def stat(self, follow_symlinks=False):
        return _FakeStat(self._attributes)

    def is_dir(self, follow_symlinks=False):
        return self._is_dir


def test_reparse_point_directory_is_skipped_and_reported(tmp_path, monkeypatch):
    root = str(tmp_path)
    junction_path = str(tmp_path / "linked")
    fake_entry = _FakeEntry(junction_path, "linked", is_dir=True, attributes=FILE_ATTRIBUTE_REPARSE_POINT)

    calls = []

    def fake_scandir(path):
        calls.append(path)
        if path == to_extended(root):
            return iter([fake_entry])
        raise AssertionError(f"should never descend into the reparse point: {path}")

    monkeypatch.setattr(walk_scanner.os, "scandir", fake_scandir)

    plan = _plan(tmp_path)
    items = list(walk_scanner.scan(plan))
    issues = [i for i in items if isinstance(i, ScanIssue)]

    assert len(calls) == 1
    assert any(i.kind == "reparse" and "linked" in i.path for i in issues)
