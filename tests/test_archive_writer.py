import os
import zipfile

import pytest

from obm.archive import writer
from obm.archive.detect import DetectedTool
from obm.archive.readme import README_NAME
from obm.archive.readme_html import HTML_NAME


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


def test_the_readme_lands_at_the_archive_root(tmp_path):
    files = _make_files(tmp_path)
    dest = tmp_path / "dest"
    tool = DetectedTool(name="zip", exe_path="")

    final = writer.write_archive(
        tool, level=1, files=files, dest_dir=str(dest), archive_filename="out.zip",
        readme_text="what is in here",
    )

    with zipfile.ZipFile(final) as zf:
        assert README_NAME in zf.namelist()
        assert zf.read(README_NAME).decode("utf-8") == "what is in here"


def test_both_readmes_land_at_the_archive_root(tmp_path):
    files = _make_files(tmp_path)
    dest = tmp_path / "dest"
    tool = DetectedTool(name="zip", exe_path="")

    final = writer.write_archive(
        tool, level=1, files=files, dest_dir=str(dest), archive_filename="out.zip",
        readme_text="what is in here", readme_html="<!doctype html><p>what is in here</p>",
    )

    with zipfile.ZipFile(final) as zf:
        assert {README_NAME, HTML_NAME} <= set(zf.namelist())
        assert zf.read(HTML_NAME).decode("utf-8").startswith("<!doctype html>")


def test_no_readme_text_means_no_readme_entry(tmp_path):
    files = _make_files(tmp_path)
    dest = tmp_path / "dest"
    tool = DetectedTool(name="zip", exe_path="")

    final = writer.write_archive(tool, level=1, files=files, dest_dir=str(dest), archive_filename="out.zip")

    with zipfile.ZipFile(final) as zf:
        assert README_NAME not in zf.namelist()


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
