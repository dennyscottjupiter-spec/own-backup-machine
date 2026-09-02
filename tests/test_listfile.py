from obm.archive.listfile import write_sevenzip_listfile, write_winrar_listfile

NAMES = ["C:\\Users\\th\u00e9o\\r\u00e9sum\u00e9.pdf", "C:\\Users\\me\\na\u00efve.txt"]


def test_sevenzip_listfile_is_utf8_no_bom():
    path = write_sevenzip_listfile(NAMES)
    try:
        raw = open(path, "rb").read()
        assert not raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8")
        for name in NAMES:
            assert name in text
    finally:
        import os
        os.remove(path)


def test_winrar_listfile_is_utf16le_with_bom():
    path = write_winrar_listfile(NAMES)
    try:
        raw = open(path, "rb").read()
        assert raw.startswith(b"\xff\xfe")
        text = raw.decode("utf-16-le")
        for name in NAMES:
            assert name in text
    finally:
        import os
        os.remove(path)
