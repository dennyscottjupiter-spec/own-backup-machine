import struct

from obm.scan.usn_records import parse_records


def _pack_record(frn, pfrn, usn, reason, attrs, name, name_offset=60, record_length=None):
    name_bytes = name.encode("utf-16-le")
    name_len = len(name_bytes)
    total = name_offset + name_len
    if record_length is None:
        record_length = total
    buf = bytearray(max(record_length, total))
    struct.pack_into("<I", buf, 0, record_length)
    struct.pack_into("<H", buf, 4, 2)  # MajorVersion
    struct.pack_into("<Q", buf, 8, frn)
    struct.pack_into("<Q", buf, 16, pfrn)
    struct.pack_into("<q", buf, 24, usn)
    struct.pack_into("<I", buf, 40, reason)
    struct.pack_into("<I", buf, 52, attrs)
    struct.pack_into("<H", buf, 56, name_len)
    struct.pack_into("<H", buf, 58, name_offset)
    buf[name_offset:name_offset + name_len] = name_bytes
    return bytes(buf[:record_length])


def test_parses_a_single_record():
    buf = _pack_record(frn=1001, pfrn=5, usn=999, reason=0x100, attrs=0x20, name="hello.txt")
    records = parse_records(buf)
    assert len(records) == 1
    r = records[0]
    assert r.file_reference_number == 1001
    assert r.parent_file_reference_number == 5
    assert r.usn == 999
    assert r.reason == 0x100
    assert r.file_attributes == 0x20
    assert r.file_name == "hello.txt"


def test_parses_multiple_concatenated_records_in_order():
    r1 = _pack_record(frn=1, pfrn=0, usn=10, reason=1, attrs=0, name="a.txt")
    r2 = _pack_record(frn=2, pfrn=0, usn=20, reason=2, attrs=0, name="b.txt")
    r3 = _pack_record(frn=3, pfrn=0, usn=30, reason=4, attrs=0, name="c.txt")
    records = parse_records(r1 + r2 + r3)
    assert [r.file_name for r in records] == ["a.txt", "b.txt", "c.txt"]
    assert [r.usn for r in records] == [10, 20, 30]


def test_honours_non_60_file_name_offset():
    buf = _pack_record(frn=7, pfrn=0, usn=1, reason=1, attrs=0, name="offset.txt", name_offset=72)
    records = parse_records(buf)
    assert len(records) == 1
    assert records[0].file_name == "offset.txt"


def test_surrogate_pair_filename_survives():
    # U+1F600 (grinning face) requires a UTF-16 surrogate pair -- exactly the kind of name
    # that silently corrupts if byte offsets are computed in characters instead of bytes.
    name = "emoji_\U0001F600.txt"
    buf = _pack_record(frn=9, pfrn=0, usn=1, reason=1, attrs=0, name=name)
    records = parse_records(buf)
    assert records[0].file_name == name


def test_truncated_trailing_record_is_dropped_not_guessed():
    good = _pack_record(frn=1, pfrn=0, usn=1, reason=1, attrs=0, name="good.txt")
    truncated = _pack_record(frn=2, pfrn=0, usn=2, reason=1, attrs=0, name="truncated.txt")
    buf = good + truncated[:20]  # claims a full record_length but the buffer ends early
    records = parse_records(buf)
    assert [r.file_name for r in records] == ["good.txt"]


def test_zero_record_length_stops_parsing():
    good = _pack_record(frn=1, pfrn=0, usn=1, reason=1, attrs=0, name="good.txt")
    zero_length = struct.pack("<I", 0) + b"\x00" * 56
    records = parse_records(good + zero_length + good)
    assert [r.file_name for r in records] == ["good.txt"]


def test_empty_buffer_returns_no_records():
    assert parse_records(b"") == []
