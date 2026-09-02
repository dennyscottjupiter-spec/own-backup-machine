# ---
# purpose: open a volume's USN journal, query it, and read raw record buffers in a loop
# exports: JournalInfo, open_volume(), query_journal(), read_buffers()
# depends: winapi/{kernel32,constants,structs}
# gotcha: no trailing backslash on \\.\C: -- with one, CreateFileW opens the root DIRECTORY and
#         the FSCTLs fail; bytes_returned <= 8 means caught up, never guess past a short read
# ---
from __future__ import annotations

import ctypes
import struct
from ctypes import wintypes
from dataclasses import dataclass
from typing import Iterator

from ..winapi import constants as c
from ..winapi import kernel32 as k32
from ..winapi.structs import READ_USN_JOURNAL_DATA_V0, USN_JOURNAL_DATA_V0

READ_BUFFER_SIZE = 1024 * 1024
QUERY_BUFFER_SIZE = 96  # Win8+ may return V1/V2; only the stable 56-byte V0 prefix is parsed


@dataclass(slots=True)
class JournalInfo:
    journal_id: int
    first_usn: int
    next_usn: int
    lowest_valid_usn: int
    max_usn: int


def open_volume(letter: str) -> int:
    path = f"\\\\.\\{letter}"
    handle = k32.CreateFileW(
        path, c.GENERIC_READ, c.FILE_SHARE_READ | c.FILE_SHARE_WRITE, None, c.OPEN_EXISTING, 0, None,
    )
    if k32.is_invalid_handle(handle):
        k32.raise_last_error(f"CreateFileW({path})")
    return handle


def query_journal(handle: int) -> JournalInfo:
    out_buf = ctypes.create_string_buffer(QUERY_BUFFER_SIZE)
    bytes_returned = wintypes.DWORD(0)
    ok = k32.DeviceIoControl(
        handle, c.FSCTL_QUERY_USN_JOURNAL, None, 0, out_buf, len(out_buf), ctypes.byref(bytes_returned), None,
    )
    if not ok:
        k32.raise_last_error("FSCTL_QUERY_USN_JOURNAL")
    data = USN_JOURNAL_DATA_V0.from_buffer_copy(out_buf.raw[: ctypes.sizeof(USN_JOURNAL_DATA_V0)])
    return JournalInfo(
        journal_id=data.UsnJournalID, first_usn=data.FirstUsn, next_usn=data.NextUsn,
        lowest_valid_usn=data.LowestValidUsn, max_usn=data.MaxUsn,
    )


def read_buffers(
    handle: int, journal_id: int, start_usn: int, reason_mask: int = c.USN_REASON_MASK
) -> Iterator[bytes]:
    usn = start_usn
    while True:
        req = READ_USN_JOURNAL_DATA_V0(
            StartUsn=usn, ReasonMask=reason_mask, ReturnOnlyOnClose=0,
            Timeout=0, BytesToWaitFor=0, UsnJournalID=journal_id,
        )
        out_buf = ctypes.create_string_buffer(READ_BUFFER_SIZE)
        bytes_returned = wintypes.DWORD(0)
        ok = k32.DeviceIoControl(
            handle, c.FSCTL_READ_USN_JOURNAL, ctypes.byref(req), ctypes.sizeof(req),
            out_buf, READ_BUFFER_SIZE, ctypes.byref(bytes_returned), None,
        )
        if not ok:
            k32.raise_last_error("FSCTL_READ_USN_JOURNAL")

        n = bytes_returned.value
        if n <= 8:
            return

        next_usn = struct.unpack_from("<q", out_buf.raw, 0)[0]
        yield out_buf.raw[8:n]
        if next_usn <= usn:
            return
        usn = next_usn
