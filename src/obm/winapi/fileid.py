# ---
# purpose: FRN -> full path via OpenFileById + GetFinalPathNameByHandleW, session-cached
# exports: FileIdResolver
# depends: kernel32.py, structs.py, constants.py
# gotcha: FILE_READ_ATTRIBUTES does not hydrate an OneDrive placeholder -- that's why it's the
#         access mask here, not GENERIC_READ; FILE_FLAG_BACKUP_SEMANTICS is mandatory since the
#         target of OpenFileById is routinely a directory
# ---
from __future__ import annotations

import ctypes

from . import constants as c
from . import kernel32 as k32
from .structs import FILE_ID_DESCRIPTOR

_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_SHARE_ALL = c.FILE_SHARE_READ | c.FILE_SHARE_WRITE | c.FILE_SHARE_DELETE
_PATH_BUF_LEN = 4096


class FileIdResolver:
    def __init__(self, volume_handle: int) -> None:
        self._volume_handle = volume_handle
        self._cache: dict[int, str | None] = {}

    def resolve(self, frn: int) -> str | None:
        if frn in self._cache:
            return self._cache[frn]
        path = self._resolve_uncached(frn)
        self._cache[frn] = path
        return path

    def _resolve_uncached(self, frn: int) -> str | None:
        desc = FILE_ID_DESCRIPTOR()
        desc.dwSize = ctypes.sizeof(FILE_ID_DESCRIPTOR)
        desc.Type = 0
        desc.u.FileId = frn if frn < 2**63 else frn - 2**64  # reinterpret unsigned FRN as signed

        handle = k32.OpenFileById(
            self._volume_handle, ctypes.byref(desc), c.FILE_READ_ATTRIBUTES,
            _SHARE_ALL, None, _FILE_FLAG_BACKUP_SEMANTICS,
        )
        if k32.is_invalid_handle(handle):
            return None
        try:
            buf = ctypes.create_unicode_buffer(_PATH_BUF_LEN)
            n = k32.GetFinalPathNameByHandleW(handle, buf, len(buf), 0)
            if n == 0 or n >= len(buf):
                return None
            return buf.value
        finally:
            k32.CloseHandle(handle)
