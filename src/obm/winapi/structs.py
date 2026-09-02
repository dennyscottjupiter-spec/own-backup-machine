# ---
# purpose: ctypes.Structure definitions for the USN journal FSCTLs and OpenFileById
# exports: USN_JOURNAL_DATA_V0, READ_USN_JOURNAL_DATA_V0, FILE_ID_DESCRIPTOR
# gotcha: FILE_ID_DESCRIPTOR's union must be sized for a GUID (16 bytes) even though only the
#         8-byte FileId variant is used -- dwSize=24 (4+4+16) is what OpenFileById expects
# ---
from __future__ import annotations

import ctypes
from ctypes import wintypes


class USN_JOURNAL_DATA_V0(ctypes.Structure):
    _fields_ = [
        ("UsnJournalID", ctypes.c_uint64),
        ("FirstUsn", ctypes.c_int64),
        ("NextUsn", ctypes.c_int64),
        ("LowestValidUsn", ctypes.c_int64),
        ("MaxUsn", ctypes.c_int64),
        ("MaximumSize", ctypes.c_uint64),
        ("AllocationDelta", ctypes.c_uint64),
    ]


class READ_USN_JOURNAL_DATA_V0(ctypes.Structure):
    _fields_ = [
        ("StartUsn", ctypes.c_int64),
        ("ReasonMask", wintypes.DWORD),
        ("ReturnOnlyOnClose", wintypes.DWORD),
        ("Timeout", ctypes.c_uint64),
        ("BytesToWaitFor", ctypes.c_uint64),
        ("UsnJournalID", ctypes.c_uint64),
    ]


class _FileIdUnion(ctypes.Union):
    _fields_ = [
        ("FileId", ctypes.c_int64),
        ("_reserved", ctypes.c_byte * 16),
    ]


class FILE_ID_DESCRIPTOR(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("Type", ctypes.c_int),  # 0 = FileIdType (a plain 64-bit FRN)
        ("u", _FileIdUnion),
    ]
