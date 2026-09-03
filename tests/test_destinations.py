from obm import destinations


def test_always_offered_drives_are_listed_first_even_when_absent(monkeypatch):
    monkeypatch.setattr(destinations, "list_drive_letters", lambda: ["C:"])
    monkeypatch.setattr(destinations, "_drive_type", lambda root: 3)

    options = destinations.drive_options()

    assert options[0] == destinations.PREFERRED_DRIVE
    assert options == ["X:\\", "D:\\", "E:\\", "C:\\"]


def test_always_offered_drives_are_not_duplicated_when_present(monkeypatch):
    monkeypatch.setattr(destinations, "list_drive_letters", lambda: ["C:", "D:", "X:"])
    monkeypatch.setattr(destinations, "_drive_type", lambda root: 3)

    assert destinations.drive_options() == ["X:\\", "D:\\", "E:\\", "C:\\"]


def test_cdrom_and_rootless_drives_are_not_offered(monkeypatch):
    types = {"C:\\": 3, "F:\\": 5, "Z:\\": 4}
    monkeypatch.setattr(destinations, "list_drive_letters", lambda: ["C:", "F:", "Z:"])
    monkeypatch.setattr(destinations, "_drive_type", lambda root: types[root])

    assert destinations.drive_options() == ["X:\\", "D:\\", "E:\\", "C:\\", "Z:\\"]


def test_desktop_and_downloads_are_offered_after_the_drives(monkeypatch):
    monkeypatch.setattr(destinations, "list_drive_letters", lambda: ["C:"])
    monkeypatch.setattr(destinations, "_drive_type", lambda root: 3)
    monkeypatch.setattr(destinations, "folder_options", lambda: ["C:\\Users\\me\\Desktop"])

    assert destinations.destination_options() == ["X:\\", "D:\\", "E:\\", "C:\\", "C:\\Users\\me\\Desktop"]


def test_an_unresolvable_folder_is_simply_not_offered(monkeypatch):
    monkeypatch.setattr(destinations, "known_folder", lambda folder_id: "")

    assert destinations.folder_options() == []


def test_configured_path_wins_over_the_preferred_drive():
    assert destinations.resolve_default("D:\\backups", ["X:\\", "C:\\"]) == "D:\\backups"


def test_blank_config_falls_back_to_the_first_option():
    assert destinations.resolve_default("   ", ["X:\\", "C:\\"]) == "X:\\"


def test_blank_config_with_no_drives_stays_blank():
    assert destinations.resolve_default("", []) == ""
