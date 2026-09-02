from obm.archive import detect


def test_detect_falls_back_to_zip_when_nothing_found(monkeypatch):
    monkeypatch.setattr(detect, "_find_sevenzip", lambda: "")
    monkeypatch.setattr(detect, "_find_winrar", lambda: "")
    result = detect.detect()
    assert result.name == "zip"
    assert result.exe_path == ""


def test_detect_prefers_sevenzip_over_winrar(monkeypatch):
    monkeypatch.setattr(detect, "_find_sevenzip", lambda: "C:\\7z.exe")
    monkeypatch.setattr(detect, "_find_winrar", lambda: "C:\\Rar.exe")
    result = detect.detect()
    assert result.name == "7z"
    assert result.exe_path == "C:\\7z.exe"


def test_detect_falls_back_to_winrar_when_no_sevenzip(monkeypatch):
    monkeypatch.setattr(detect, "_find_sevenzip", lambda: "")
    monkeypatch.setattr(detect, "_find_winrar", lambda: "C:\\Rar.exe")
    result = detect.detect()
    assert result.name == "rar"
    assert result.exe_path == "C:\\Rar.exe"
