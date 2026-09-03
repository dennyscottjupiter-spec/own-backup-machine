from obm.models import CandidateFile
from obm.ui.charts.treemap_model import build_tree
from obm.winapi.constants import FILE_ATTRIBUTE_OFFLINE


def _candidate(path, size, verdict="keep", tags=frozenset()):
    return CandidateFile(path=path, volume="C:", size=size, mtime_ns=1, attributes=0,
                          source="walk", verdict=verdict, tags=tags)


def test_builds_nested_directories_with_subtree_sums():
    candidates = [
        _candidate("C:\\a\\b\\f1.txt", 100),
        _candidate("C:\\a\\b\\f2.txt", 200),
        _candidate("C:\\a\\f3.txt", 50),
    ]
    root = build_tree(candidates)
    a = next(c for c in root.children if c.name == "C:")
    a = next(c for c in a.children if c.name == "a")
    assert a.size == 350
    b = next(c for c in a.children if c.name == "b")
    assert b.size == 300
    assert {c.name for c in b.children} == {"f1.txt", "f2.txt"}


def test_children_sorted_descending_by_size():
    candidates = [
        _candidate("C:\\small.txt", 10),
        _candidate("C:\\big.txt", 1000),
        _candidate("C:\\medium.txt", 100),
    ]
    root = build_tree(candidates)
    c_drive = next(c for c in root.children if c.name == "C:")
    sizes = [c.size for c in c_drive.children]
    assert sizes == sorted(sizes, reverse=True)


def test_dropped_candidates_excluded_by_default():
    candidates = [_candidate("C:\\dropped.log", 10, verdict="drop")]
    root = build_tree(candidates)
    assert root.children == []


def test_dropped_candidates_included_when_requested_and_tagged_filtered():
    candidates = [_candidate("C:\\dropped.log", 10, verdict="drop")]
    root = build_tree(candidates, include_dropped=True)
    c_drive = root.children[0]
    leaf = c_drive.children[0]
    assert leaf.category == "filtered"


def test_placeholders_always_excluded_even_when_dropped_included():
    candidates = [_candidate("C:\\cloud.txt", 10, tags=frozenset({"placeholder"}))]
    root = build_tree(candidates, include_dropped=True)
    assert root.children == []


def test_deselected_candidates_dropped_when_selected_only():
    candidates = [_candidate("C:\\keep.jpg", 100), _candidate("C:\\skip.jpg", 200)]
    candidates[1].selected = False
    root = build_tree(candidates, selected_only=True)
    c_drive = root.children[0]
    assert [c.name for c in c_drive.children] == ["keep.jpg"]
    assert c_drive.size == 100


def test_selected_only_does_not_hide_dropped_files_shown_on_request():
    """`selected` is only meaningful for kept files -- the filtered view must still show drops."""
    candidates = [_candidate("C:\\dropped.log", 10, verdict="drop")]
    candidates[0].selected = False
    root = build_tree(candidates, include_dropped=True, selected_only=True)
    assert root.children[0].children[0].category == "filtered"
