import os

import pytest

from obm.archive import writer
from obm.archive.detect import DetectedTool


def _make_files(tmp_path):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("alpha")
    f2.write_text("bravo")
    return [str(f1), str(f2)]


def test_zip_roundtrip_creates_verified_archive(tmp_path):
    files = _make_files(tmp_path)
    dest = tmp_path / "dest"
    tool = DetectedTool(name="zip", exe_path="")

    final = writer.write_archive(tool, level=1, files=files, dest_dir=str(dest), archive_filename="out.zip")

    assert os.path.exists(final)
    assert not os.path.exists(final + ".part")


def test_verify_failure_leaves_no_final_file(tmp_path, monkeypatch):
    files = _make_files(tmp_path)
    dest = tmp_path / "dest"
    tool = DetectedTool(name="zip", exe_path="")

    monkeypatch.setattr(writer._BACKENDS["zip"], "verify", lambda exe_path, archive_path: False)

    with pytest.raises(RuntimeError):
        writer.write_archive(tool, level=1, files=files, dest_dir=str(dest), archive_filename="out.zip")

    final = dest / "out.zip"
    assert not final.exists()
    assert not (dest / "out.zip.part").exists()


def test_dropped_destination_leaves_only_a_part_file(tmp_path, monkeypatch):
    files = _make_files(tmp_path)
    dest = tmp_path / "dest"
    tool = DetectedTool(name="zip", exe_path="")

    real_replace = os.replace

    def boom(*args, **kwargs):
        raise OSError("simulated dropped network drive")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        writer.write_archive(tool, level=1, files=files, dest_dir=str(dest), archive_filename="out.zip")
    monkeypatch.setattr(os, "replace", real_replace)

    final = dest / "out.zip"
    part = dest / "out.zip.part"
    assert not final.exists()
    assert part.exists()
