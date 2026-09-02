from obm.models import ScanIssue
from obm.scan.issues import report


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
    assert "[Access denied] C:\\b.txt — winerror 5" in lines
    assert "[Path too long] C:\\c.txt" in lines


def test_unknown_kind_falls_back_to_the_raw_kind():
    text = report([ScanIssue(path="C:\\a.txt", kind="weird")])
    assert "[weird] C:\\a.txt" in text
