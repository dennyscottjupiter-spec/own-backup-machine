from obm.models import CandidateFile
from obm.pipeline.selection import selected_files


def _candidate(verdict="keep", selected=True):
    return CandidateFile(path="C:\\f.txt", volume="C:", size=1, mtime_ns=1, attributes=0,
                          source="walk", verdict=verdict, selected=selected)


def test_keeps_only_keep_verdict_and_selected():
    candidates = [
        _candidate(verdict="keep", selected=True),
        _candidate(verdict="keep", selected=False),
        _candidate(verdict="drop", selected=True),
        _candidate(verdict="drop", selected=False),
    ]
    result = selected_files(candidates)
    assert len(result) == 1
    assert result[0].verdict == "keep"
    assert result[0].selected is True


def test_empty_input_returns_empty_list():
    assert selected_files([]) == []
