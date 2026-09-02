from obm import destinations


def test_preferred_drive_is_listed_first_even_when_absent(monkeypatch):
    monkeypatch.setattr(destinations, "list_drive_letters", lambda: ["C:", "D:"])
    monkeypatch.setattr(destinations, "_drive_type", lambda root: 3)

    options = destinations.drive_options()

    assert options[0] == destinations.PREFERRED_DRIVE
    assert options == ["X:\\", "C:\\", "D:\\"]


def test_preferred_drive_is_not_duplicated_when_present(monkeypatch):
    monkeypatch.setattr(destinations, "list_drive_letters", lambda: ["C:", "X:"])
    monkeypatch.setattr(destinations, "_drive_type", lambda root: 3)

    assert destinations.drive_options() == ["X:\\", "C:\\"]


def test_cdrom_and_rootless_drives_are_not_offered(monkeypatch):
    types = {"C:\\": 3, "E:\\": 5, "Z:\\": 4}
    monkeypatch.setattr(destinations, "list_drive_letters", lambda: ["C:", "E:", "Z:"])
    monkeypatch.setattr(destinations, "_drive_type", lambda root: types[root])

    assert destinations.drive_options() == ["X:\\", "C:\\", "Z:\\"]


def test_configured_path_wins_over_the_preferred_drive():
    assert destinations.resolve_default("D:\\backups", ["X:\\", "C:\\"]) == "D:\\backups"


def test_blank_config_falls_back_to_the_first_option():
    assert destinations.resolve_default("   ", ["X:\\", "C:\\"]) == "X:\\"


def test_blank_config_with_no_drives_stays_blank():
    assert destinations.resolve_default("", []) == ""
