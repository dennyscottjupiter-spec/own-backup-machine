from obm.winapi.longpath import to_display, to_extended


def test_plain_path_gets_prefixed():
    assert to_extended("C:\\Users\\me\\file.txt") == "\\\\?\\C:\\Users\\me\\file.txt"


def test_already_extended_is_unchanged():
    p = "\\\\?\\C:\\Users\\me\\file.txt"
    assert to_extended(p) == p


def test_unc_path_gets_unc_prefix():
    assert to_extended("\\\\server\\share\\file.txt") == "\\\\?\\UNC\\server\\share\\file.txt"


def test_normalizes_dot_dot_before_prefixing():
    assert to_extended("C:\\Users\\me\\..\\me\\file.txt") == "\\\\?\\C:\\Users\\me\\file.txt"


def test_to_display_strips_plain_prefix():
    assert to_display("\\\\?\\C:\\Users\\me\\file.txt") == "C:\\Users\\me\\file.txt"


def test_to_display_strips_unc_prefix():
    assert to_display("\\\\?\\UNC\\server\\share\\file.txt") == "\\\\server\\share\\file.txt"


def test_to_display_passthrough_for_plain_path():
    assert to_display("C:\\Users\\me\\file.txt") == "C:\\Users\\me\\file.txt"


def test_roundtrip():
    original = "C:\\Users\\me\\file.txt"
    assert to_display(to_extended(original)) == original
