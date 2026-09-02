# ---
# purpose: pure bytes -> USN_RECORD_V2 parser, no Win32 calls
# exports: UsnRecord, parse_records()
# gotcha: ALWAYS honour FileNameOffset, never assume 60 -- and FileNameLength is in BYTES
#         (UTF-16LE), not characters. A RecordLength of 0 or a record past bytes_returned
#         means a truncated buffer: stop, don't guess.
# ---
from __future__ import annotations

import struct
from dataclasses import dataclass


@dataclass(slots=True)
class UsnRecord:
    record_length: int
    file_reference_number: int
    parent_file_reference_number: int
    usn: int
    reason: int
    file_attributes: int
    file_name: str


def parse_records(buffer: bytes) -> list[UsnRecord]:
    records: list[UsnRecord] = []
    offset = 0
    n = len(buffer)

    while offset + 60 <= n:
        record_length = struct.unpack_from("<I", buffer, offset)[0]
        if record_length == 0 or offset + record_length > n:
            break

        frn = struct.unpack_from("<Q", buffer, offset + 8)[0]
        pfrn = struct.unpack_from("<Q", buffer, offset + 16)[0]
        usn = struct.unpack_from("<q", buffer, offset + 24)[0]
        reason = struct.unpack_from("<I", buffer, offset + 40)[0]
        attrs = struct.unpack_from("<I", buffer, offset + 52)[0]
        name_len = struct.unpack_from("<H", buffer, offset + 56)[0]
        name_off = struct.unpack_from("<H", buffer, offset + 58)[0]

        name_start = offset + name_off
        name_end = name_start + name_len
        if name_end > offset + record_length:
            break  # truncated trailing record

        name = buffer[name_start:name_end].decode("utf-16-le", errors="replace")
        records.append(UsnRecord(
            record_length=record_length, file_reference_number=frn, parent_file_reference_number=pfrn,
            usn=usn, reason=reason, file_attributes=attrs, file_name=name,
        ))
        offset += record_length

    return records
