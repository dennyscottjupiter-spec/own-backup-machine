from obm.models import CandidateFile
from obm.palette import CATEGORY_COLORS, dim
from obm.pipeline.aggregate import build_summary


def _candidate(path, size, verdict="keep", selected=True, tags=frozenset()):
    return CandidateFile(path=path, volume="C:", size=size, mtime_ns=1, attributes=0,
                         source="walk", verdict=verdict, selected=selected, tags=tags)


def _summary(candidates):
    return build_summary(candidates, [])


def test_selected_totals_are_a_subset_of_kept():
    s = _summary([
        _candidate("C:\\a.mp4", 100, selected=True),
        _candidate("C:\\b.mp4", 30, selected=False),
    ])
    assert (s.kept_count, s.kept_bytes) == (2, 130)
    assert (s.selected_count, s.selected_bytes) == (1, 100)


def test_deselecting_never_moves_bytes_into_dropped():
    """The scan totals are the reference the UI shows alongside the live figure -- a checkbox
    press must not make a kept file look like a blocklisted one."""
    before = _summary([_candidate("C:\\a.mp4", 100, selected=True)])
    after = _summary([_candidate("C:\\a.mp4", 100, selected=False)])
    assert after.kept_bytes == before.kept_bytes == 100
    assert after.dropped_bytes == before.dropped_bytes == 0
    assert after.selected_bytes == 0


def test_by_category_selected_tracks_only_ticked_files():
    s = _summary([
        _candidate("C:\\a.mp4", 100, selected=True),
        _candidate("C:\\b.mp4", 30, selected=False),
        _candidate("C:\\c.txt", 7, selected=False),
    ])
    assert s.by_category["video"] == (2, 130)
    assert s.by_category_selected["video"] == (1, 100)
    # a fully deselected category keeps its scan row and loses its selected row entirely
    assert s.by_category["document"] == (1, 7)
    assert "document" not in s.by_category_selected


def test_dropped_and_placeholder_files_never_reach_the_selected_totals():
    s = _summary([
        _candidate("C:\\junk.tmp", 50, verdict="drop", selected=True),
        _candidate("C:\\cloud.mp4", 60, tags=frozenset({"placeholder"}), selected=True),
    ])
    assert (s.selected_count, s.selected_bytes) == (0, 0)
    assert s.dropped_bytes == 50
    assert s.placeholder_count == 1


def test_dim_darkens_a_category_colour_without_changing_its_hue():
    dark = dim(CATEGORY_COLORS["video"])  # #ef4444
    assert dark.startswith("#") and len(dark) == 7
    r, g, b = (int(dark[i:i + 2], 16) for i in (1, 3, 5))
    assert r > g == b  # still red-dominant
    assert r < 0xEF  # but darker than the full-strength colour
