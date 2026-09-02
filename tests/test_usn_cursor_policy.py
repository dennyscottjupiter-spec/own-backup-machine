from obm.state.cursors import decide
from obm.state.schema import VolumeState


def _stored(journal_id=1, next_usn=1000) -> VolumeState:
    return VolumeState(guid_path="G", letter="C:", last_run_utc="2026-01-01T00:00:00+00:00",
                        journal_id=journal_id, next_usn=next_usn)


def test_no_stored_entry_is_first_run():
    method, reason = decide(None, queried_journal_id=1, queried_lowest_valid_usn=0, queried_next_usn=1000)
    assert method == "walk"
    assert reason == "first run"


def test_journal_id_mismatch_is_recreated():
    method, reason = decide(_stored(journal_id=1), queried_journal_id=2,
                             queried_lowest_valid_usn=0, queried_next_usn=1000)
    assert method == "walk"
    assert reason == "journal recreated"


def test_cursor_below_lowest_valid_is_wrapped():
    method, reason = decide(_stored(next_usn=100), queried_journal_id=1,
                             queried_lowest_valid_usn=500, queried_next_usn=1000)
    assert method == "walk"
    assert reason == "journal wrapped past cursor"


def test_cursor_above_next_usn_is_rewound():
    method, reason = decide(_stored(next_usn=2000), queried_journal_id=1,
                             queried_lowest_valid_usn=0, queried_next_usn=1000)
    assert method == "walk"
    assert reason == "journal rewound"


def test_valid_cursor_uses_usn():
    method, reason = decide(_stored(journal_id=1, next_usn=1000), queried_journal_id=1,
                             queried_lowest_valid_usn=0, queried_next_usn=1500)
    assert method == "usn"
    assert reason == "cursor valid"
