import re
from datetime import datetime

from obm.archive import readme_html
from obm.models import CandidateFile


def _file(path, size=100):
    return CandidateFile(path=path, volume="C:", size=size, mtime_ns=0, attributes=0, source="walk")


def _build(files):
    return readme_html.build(
        archive_name="own-backup-machine_20260903_120000_000.zip",
        run_id="20260903_120000_000",
        created=datetime(2026, 9, 3, 12, 0, 0),
        tool_label="zip level 5",
        files=files,
    )


def test_the_page_is_self_contained_and_offline():
    html = _build([_file("C:\\Users\\me\\a.docx", 2048)])

    assert html.startswith("<!doctype html>")
    assert "<style>" in html and "<script>" in html
    # nothing may be fetched: this page is opened from inside an archive, often with no network
    assert not re.search(r'(src|href)\s*=\s*"(?!#)', html)
    assert "http://" not in html and "https://" not in html


def test_the_header_states_what_the_run_produced():
    html = _build([_file("C:\\Users\\me\\a.docx", 1024), _file("C:\\Users\\me\\b.docx", 1024)])

    assert "<title>own-backup-machine_20260903_120000_000.zip</title>" in html
    assert "<dd>20260903_120000_000</dd>" in html
    assert "<dd>2</dd>" in html
    assert "<dd>2.0 KB</dd>" in html
    assert "own-backup-machine_20260903_120000_000.zip.manifest.json" in html


def test_folders_carry_their_own_totals_and_a_size_share():
    html = _build([_file("C:\\Users\\me\\pics\\a.jpg", 900), _file("C:\\Users\\me\\docs\\b.docx", 100)])

    assert "pics\\</span><span class=\"n\">1 file</span><span class=\"sz\">900 B</span>" in html
    assert "--w:90" in html  # pics is 90% of its parent


def test_a_single_child_chain_is_folded_into_one_row():
    html = _build([_file("C:\\Users\\me\\deep\\down\\here\\a.txt")])

    assert "C:\\Users\\me\\deep\\down\\here\\" in html


def test_every_row_is_searchable_by_its_lowercased_path():
    html = _build([_file("C:\\Users\\Me\\Photos\\Trip.JPG")])

    assert 'data-p="c:\\users\\me\\photos\\trip.jpg"' in html
    assert 'data-p="c:\\users\\me\\photos\\"' in html


def test_the_flat_list_is_capped_and_points_at_the_text_index(monkeypatch):
    monkeypatch.setattr(readme_html, "FILE_ROW_CAP", 3)
    html = _build([_file(f"C:\\Users\\me\\f{i}.txt", 10 - i) for i in range(6)])

    listing = html.split('<div class="tree files">')[1]
    assert listing.count('class="row"') == 3
    assert "3 of 6 files are listed here" in html
    assert "The other 3 are in BACKUP-README.txt" in html


def test_a_path_with_html_in_it_cannot_break_the_page():
    html = _build([_file('C:\\Users\\me\\<script>alert("x")</script>.txt')])

    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html


def test_an_empty_run_still_renders():
    html = _build([])

    assert "This run archived nothing." in html
    assert "<dd>0</dd>" in html
