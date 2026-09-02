import os

from obm import paths
from obm.state import store
from obm.state.schema import AppState, VolumeState


def test_load_missing_file_returns_empty_state(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)
    state = store.load()
    assert state.schema_version == 1
    assert state.volumes == {}


def test_save_then_load_roundtrips(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)
    state = AppState()
    state.volumes["G1"] = VolumeState(guid_path="G1", letter="C:", last_run_utc="2026-01-01T00:00:00+00:00",
                                       journal_id=7, next_usn=42)
    store.save(state)

    loaded = store.load()
    assert loaded.volumes["G1"].letter == "C:"
    assert loaded.volumes["G1"].journal_id == 7
    assert loaded.volumes["G1"].next_usn == 42


def test_failed_write_leaves_old_state_intact(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)

    good_state = AppState()
    good_state.volumes["G1"] = VolumeState(guid_path="G1", letter="C:", last_run_utc="2026-01-01T00:00:00+00:00")
    store.save(good_state)

    real_replace = os.replace

    def boom(*args, **kwargs):
        raise OSError("simulated crash before replace")

    monkeypatch.setattr(os, "replace", boom)
    bad_state = AppState()
    bad_state.volumes["G2"] = VolumeState(guid_path="G2", letter="D:", last_run_utc="2026-01-02T00:00:00+00:00")
    try:
        store.save(bad_state)
    except OSError:
        pass
    monkeypatch.setattr(os, "replace", real_replace)

    reloaded = store.load()
    assert "G1" in reloaded.volumes
    assert "G2" not in reloaded.volumes

    leftover_tmp_files = [f for f in os.listdir(tmp_path) if f.startswith(".state-")]
    assert leftover_tmp_files == []
