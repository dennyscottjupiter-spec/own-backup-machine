from obm.models import ScanIssue
from obm.scan.issues import by_size, report, resolve_sizes, size_prefix


def test_report_is_empty_marker_when_there_are_no_issues():
    assert report([]) == "No issues."


def test_report_counts_by_kind_then_lists_every_issue():
    issues = [
        ScanIssue(path="C:\\a.txt", kind="denied"),
        ScanIssue(path="C:\\b.txt", kind="denied", detail="winerror 5"),
        ScanIssue(path="C:\\c.txt", kind="toolong"),
    ]

    text = report(issues)
    lines = text.splitlines()

    assert lines[0] == "3 scan issues — Access denied: 2, Path too long: 1"
    assert "[?] [Access denied] C:\\b.txt — winerror 5" in lines
    assert "[?] [Path too long] C:\\c.txt" in lines


def test_unknown_kind_falls_back_to_the_raw_kind():
    text = report([ScanIssue(path="C:\\a.txt", kind="weird")])
    assert "[weird] C:\\a.txt" in text


def test_report_lists_the_biggest_issue_first():
    issues = [
        ScanIssue(path="C:\\small.txt", kind="locked", size=10),
        ScanIssue(path="C:\\huge.txt", kind="locked", size=5_000_000),
        ScanIssue(path="C:\\unknown.txt", kind="vanished"),
    ]

    body = report(issues).splitlines()[2:]

    assert body[0].endswith("C:\\huge.txt")
    assert body[1].endswith("C:\\small.txt")
    assert body[2] == "[?] [Vanished during scan] C:\\unknown.txt"


def test_by_size_sorts_biggest_first_and_leaves_unknown_sizes_last():
    a = ScanIssue(path="a", kind="denied", size=0)
    b = ScanIssue(path="b", kind="denied", size=7)

    assert by_size([a, b]) == [b, a]


def test_size_prefix_is_human_readable():
    assert size_prefix(ScanIssue(path="a", kind="denied", size=2048)) == "2.0 KB"
    assert size_prefix(ScanIssue(path="a", kind="denied")) == "?"


def test_resolve_sizes_fills_real_files_and_leaves_missing_ones_at_zero(tmp_path):
    real = tmp_path / "real.bin"
    real.write_bytes(b"x" * 123)
    issues = [
        ScanIssue(path=str(real), kind="locked"),
        ScanIssue(path=str(tmp_path / "gone.bin"), kind="vanished"),
    ]

    resolve_sizes(issues)

    assert issues[0].size == 123
    assert issues[1].size == 0


def test_resolve_sizes_stops_at_the_lookup_cap(tmp_path):
    real = tmp_path / "real.bin"
    real.write_bytes(b"x" * 5)
    issues = [ScanIssue(path=str(real), kind="locked") for _ in range(3)]

    resolve_sizes(issues, limit=1)

    assert [i.size for i in issues] == [5, 0, 0]
