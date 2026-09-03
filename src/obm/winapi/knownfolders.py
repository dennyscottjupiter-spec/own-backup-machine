# ---
# purpose: resolve Desktop and Downloads through SHGetKnownFolderPath
# exports: DESKTOP, DOWNLOADS, known_folder()
# gotcha: %USERPROFILE%\Desktop is a guess, not the answer -- OneDrive Backup redirects Desktop
#         and Downloads elsewhere, and Downloads has no environment variable at all. The returned
#         buffer is CoTaskMem and must be freed, or every call leaks a path.
# ---
from __future__ import annotations

import ctypes
from ctypes import wintypes

_ole32 = ctypes.WinDLL("ole32", use_last_error=True)
_shell32 = ctypes.WinDLL("shell32", use_last_error=True)

DESKTOP = "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"
DOWNLOADS = "{374DE290-123F-4565-9164-39C4925E467B}"

_CLSIDFromString = _ole32.CLSIDFromString
_CLSIDFromString.argtypes = [wintypes.LPCWSTR, ctypes.c_char_p]
_CLSIDFromString.restype = ctypes.c_long

_CoTaskMemFree = _ole32.CoTaskMemFree
_CoTaskMemFree.argtypes = [ctypes.c_void_p]
_CoTaskMemFree.restype = None

_SHGetKnownFolderPath = _shell32.SHGetKnownFolderPath
_SHGetKnownFolderPath.argtypes = [ctypes.c_char_p, wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)]
_SHGetKnownFolderPath.restype = ctypes.c_long


def known_folder(folder_id: str) -> str:
    """The folder's real path, or "" if Windows cannot resolve it."""
    clsid = ctypes.create_string_buffer(16)
    if _CLSIDFromString(folder_id, clsid) != 0:
        return ""
    out = ctypes.c_wchar_p()
    if _SHGetKnownFolderPath(clsid, 0, None, ctypes.byref(out)) != 0:
        return ""
    try:
        return out.value or ""
    finally:
        _CoTaskMemFree(out)
