from obm import config as config_mod
from obm import paths


def test_layout_roundtrips_through_config_toml(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)
    cfg = config_mod.Config(
        destination_path="D:\\backups",
        layout_geometry="1400x900+20+10",
        layout_main_sashes=[512],
        layout_left_sashes=[300, 470],
    )

    config_mod.save(cfg)
    loaded = config_mod.load()

    assert loaded.layout_geometry == "1400x900+20+10"
    assert loaded.layout_main_sashes == [512]
    assert loaded.layout_left_sashes == [300, 470]


def test_a_config_without_layout_keys_loads_with_empty_layout(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)
    (tmp_path / "config.toml").write_text("[ui]\nbig_file_mb = 250\n", encoding="utf-8")

    loaded = config_mod.load()

    assert loaded.big_file_mb == 250
    assert loaded.layout_geometry == ""
    assert loaded.layout_main_sashes == []
    assert loaded.layout_left_sashes == []
