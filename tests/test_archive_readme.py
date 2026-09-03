from datetime import datetime

from obm.archive import readme
from obm.models import CandidateFile


def _file(path, size=100):
    return CandidateFile(path=path, volume="C:", size=size, mtime_ns=0, attributes=0, source="walk")


def _build(files):
    return readme.build(
        archive_name="own-backup-machine_20260903_120000_000.zip",
        run_id="20260903_120000_000",
        created=datetime(2026, 9, 3, 12, 0, 0),
        tool_label="zip level 5",
        files=files,
    )


def test_front_matter_leads_with_the_counts_and_the_run_identity():
    text = _build([_file("C:\\Users\\me\\a.docx", 1024), _file("C:\\Users\\me\\b.docx", 1024)])
    lines = text.splitlines()

    assert lines[0] == "---"
    assert "archive:  own-backup-machine_20260903_120000_000.zip" in lines
    assert "run id:   20260903_120000_000" in lines
    assert "files:    2" in lines
    assert "size:     2.0 KB before compression" in lines
    assert lines[7] == "---"


def test_it_breaks_the_contents_down_by_kind():
    text = _build([_file("C:\\a.docx"), _file("C:\\b.jpg"), _file("C:\\c.jpg")])

    kinds = text.split("WHAT KIND OF FILES")[1].split("WHERE THE FILES CAME FROM")[0]
    assert "photo              2 files   200 B" in kinds
    assert "document            1 file   100 B" in kinds


def test_the_folder_tree_shows_every_level_with_its_own_totals():
    files = [
        _file("C:\\Users\\me\\Docs\\a.docx", 10),
        _file("C:\\Users\\me\\Docs\\deep\\b.docx", 20),
        _file("C:\\Users\\me\\c.docx", 30),
    ]

    tree = _build(files).split("WHERE THE FILES CAME FROM")[1].split("EVERY FILE")[0]
    rows = [line.strip() for line in tree.splitlines() if line.strip()]

    assert rows[0].startswith("C:\\Users\\me\\") and rows[0].endswith("3 files   60 B")
    assert any(r.startswith("Docs\\") and r.endswith("2 files   30 B") for r in rows)
    assert any(r.startswith("deep\\") and r.endswith("1 file   20 B") for r in rows)


def test_a_folder_that_only_leads_to_one_other_folder_is_joined_onto_it():
    files = [_file("C:\\Users\\me\\AppData\\Local\\Temp\\a.tmp")]

    tree = _build(files).split("WHERE THE FILES CAME FROM")[1].split("EVERY FILE")[0]
    rows = [line.strip() for line in tree.splitlines() if line.strip()]

    assert len(rows) == 1
    assert rows[0].startswith("C:\\Users\\me\\AppData\\Local\\Temp\\")


def test_a_folder_holding_its_own_files_is_never_folded_away():
    files = [_file("C:\\data\\keep.txt"), _file("C:\\data\\sub\\deeper.txt")]

    tree = _build(files).split("WHERE THE FILES CAME FROM")[1].split("EVERY FILE")[0]
    rows = [line.strip() for line in tree.splitlines() if line.strip()]

    assert rows[0].startswith("C:\\data\\") and not rows[0].startswith("C:\\data\\sub")
    assert rows[1].startswith("sub\\")


def test_the_biggest_folder_is_listed_first():
    files = [_file("C:\\small\\a.txt", 1), _file("C:\\huge\\b.txt", 999)]

    tree = _build(files).split("WHERE THE FILES CAME FROM")[1].split("EVERY FILE")[0]
    rows = [line.strip() for line in tree.splitlines() if line.strip()]

    assert rows[1].startswith("huge\\")
    assert rows[2].startswith("small\\")


def test_every_file_is_listed_with_its_size():
    text = _build([_file("C:\\Users\\me\\a.docx", 2048)])

    listing = text.split("EVERY FILE IN THIS ARCHIVE")[1]
    assert "[2.0 KB]" in listing
    assert "C:\\Users\\me\\a.docx" in listing


def test_it_points_at_the_json_sidecar_by_name():
    text = _build([_file("C:\\a.docx")])

    assert "own-backup-machine_20260903_120000_000.zip.manifest.json" in text


def test_an_empty_run_still_produces_a_readable_file():
    text = _build([])

    assert "files:    0" in text
    assert "(nothing was archived in this run)" in text


def test_write_temp_puts_the_text_under_the_real_readme_name(tmp_path):
    path = readme.write_temp("hello")

    assert path.endswith(readme.README_NAME)
    with open(path, encoding="utf-8") as f:
        assert f.read() == "hello"
