from obm import paths
from obm.models import RunRecord
from obm.state import history


def _record(run_id, archive_path):
    return RunRecord(run_id=run_id, started_utc="t0", finished_utc="t1", status="ok",
                      archive_path=archive_path, file_count=1, total_bytes=10, issue_count=0)


def test_append_then_load(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)
    history.append(_record("r1", str(tmp_path / "r1.zip")))
    history.append(_record("r2", str(tmp_path / "r2.zip")))

    records = history.load()
    assert [r.run_id for r in records] == ["r1", "r2"]


def test_locate_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)
    assert history.locate("missing") is None


def test_delete_removes_record_and_archive_file(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)
    archive = tmp_path / "r1.zip"
    archive.write_text("data")
    history.append(_record("r1", str(archive)))

    assert history.delete("r1") is True
    assert history.locate("r1") is None
    assert not archive.exists()


def test_delete_unknown_run_returns_false(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)
    assert history.delete("nope") is False
