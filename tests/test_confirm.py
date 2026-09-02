from obm.models import CandidateFile
from obm.scan import confirm as confirm_mod


class FakeFingerprints:
    def __init__(self, row):
        self._row = row

    def lookup(self, path):
        return self._row


def _candidate(size=100, mtime_ns=1, attributes=0):
    return CandidateFile(path="C:\\f.txt", volume="C:", size=size, mtime_ns=mtime_ns, attributes=attributes, source="walk")


def test_no_row_keeps_without_hashing(monkeypatch):
    calls = []
    monkeypatch.setattr(confirm_mod, "hash_file", lambda p: calls.append(p) or "x")
    assert confirm_mod.confirm(_candidate(), FakeFingerprints(None), hash_max_mb=512) is True
    assert calls == []


def test_size_and_mtime_match_drops_without_hashing(monkeypatch):
    calls = []
    monkeypatch.setattr(confirm_mod, "hash_file", lambda p: calls.append(p) or "x")
    fp = FakeFingerprints((100, 1, "somehash"))
    assert confirm_mod.confirm(_candidate(size=100, mtime_ns=1), fp, hash_max_mb=512) is False
    assert calls == []


def test_size_mismatch_keeps_without_hashing(monkeypatch):
    calls = []
    monkeypatch.setattr(confirm_mod, "hash_file", lambda p: calls.append(p) or "x")
    fp = FakeFingerprints((999, 1, "somehash"))
    assert confirm_mod.confirm(_candidate(size=100, mtime_ns=1), fp, hash_max_mb=512) is True
    assert calls == []


def test_placeholder_never_hashed_even_when_ambiguous(monkeypatch):
    from obm.winapi.constants import FILE_ATTRIBUTE_OFFLINE

    calls = []
    monkeypatch.setattr(confirm_mod, "hash_file", lambda p: calls.append(p) or "x")
    fp = FakeFingerprints((100, 1, "somehash"))
    cand = _candidate(size=100, mtime_ns=2, attributes=FILE_ATTRIBUTE_OFFLINE)
    assert confirm_mod.confirm(cand, fp, hash_max_mb=512) is True
    assert calls == []


def test_oversized_file_never_hashed_even_when_ambiguous(monkeypatch):
    calls = []
    monkeypatch.setattr(confirm_mod, "hash_file", lambda p: calls.append(p) or "x")
    fp = FakeFingerprints((100, 1, "somehash"))
    cand = _candidate(size=100, mtime_ns=2)
    assert confirm_mod.confirm(cand, fp, hash_max_mb=0) is True
    assert calls == []


def test_ambiguous_small_file_is_hashed_and_compared(monkeypatch):
    monkeypatch.setattr(confirm_mod, "hash_file", lambda p: "newhash")
    fp = FakeFingerprints((100, 1, "oldhash"))
    cand = _candidate(size=100, mtime_ns=2)
    assert confirm_mod.confirm(cand, fp, hash_max_mb=512) is True
    assert cand.content_hash == "newhash"

    fp_same = FakeFingerprints((100, 1, "newhash"))
    cand2 = _candidate(size=100, mtime_ns=2)
    assert confirm_mod.confirm(cand2, fp_same, hash_max_mb=512) is False
