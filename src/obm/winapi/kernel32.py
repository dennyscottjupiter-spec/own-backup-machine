# ---
# purpose: ctypes bindings to kernel32.dll with explicit argtypes/restype + WinError raiser
# exports: raise_last_error(), CreateFileW, CloseHandle, DeviceIoControl, GetLogicalDriveStringsW,
#          GetDriveTypeW, GetVolumeInformationW, GetVolumeNameForVolumeMountPointW,
#          OpenFileById, GetFinalPathNameByHandleW, IsUserAnAdmin
# gotcha: every restype is explicit — an unset restype truncates 64-bit handles to 32 bits
# ---
from __future__ import annotations

import ctypes
from ctypes import wintypes

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_shell32 = ctypes.WinDLL("shell32", use_last_error=True)

LPSECURITY_ATTRIBUTES = ctypes.c_void_p
HANDLE = wintypes.HANDLE


def raise_last_error(context: str = "") -> None:
    err = ctypes.get_last_error()
    raise ctypes.WinError(err, f"{context} (GetLastError={err})" if context else None)


CreateFileW = _k32.CreateFileW
CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    LPSECURITY_ATTRIBUTES,
    wintypes.DWORD,
    wintypes.DWORD,
    HANDLE,
]
CreateFileW.restype = HANDLE

CloseHandle = _k32.CloseHandle
CloseHandle.argtypes = [HANDLE]
CloseHandle.restype = wintypes.BOOL

DeviceIoControl = _k32.DeviceIoControl
DeviceIoControl.argtypes = [
    HANDLE,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
DeviceIoControl.restype = wintypes.BOOL

GetLogicalDriveStringsW = _k32.GetLogicalDriveStringsW
GetLogicalDriveStringsW.argtypes = [wintypes.DWORD, wintypes.LPWSTR]
GetLogicalDriveStringsW.restype = wintypes.DWORD

GetDriveTypeW = _k32.GetDriveTypeW
GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
GetDriveTypeW.restype = wintypes.UINT

GetVolumeInformationW = _k32.GetVolumeInformationW
GetVolumeInformationW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPWSTR,
    wintypes.DWORD,
]
GetVolumeInformationW.restype = wintypes.BOOL

GetVolumeNameForVolumeMountPointW = _k32.GetVolumeNameForVolumeMountPointW
GetVolumeNameForVolumeMountPointW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.DWORD,
]
GetVolumeNameForVolumeMountPointW.restype = wintypes.BOOL

OpenFileById = _k32.OpenFileById
OpenFileById.argtypes = [
    HANDLE,
    wintypes.LPVOID,  # LPFILE_ID_DESCRIPTOR, defined in structs.py
    wintypes.DWORD,
    wintypes.DWORD,
    LPSECURITY_ATTRIBUTES,
    wintypes.DWORD,
]
OpenFileById.restype = HANDLE

GetFinalPathNameByHandleW = _k32.GetFinalPathNameByHandleW
GetFinalPathNameByHandleW.argtypes = [
    HANDLE,
    wintypes.LPWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
]
GetFinalPathNameByHandleW.restype = wintypes.DWORD

IsUserAnAdmin = _shell32.IsUserAnAdmin
IsUserAnAdmin.argtypes = []
IsUserAnAdmin.restype = wintypes.BOOL


def is_invalid_handle(h: int) -> bool:
    return ctypes.c_ssize_t(h).value == -1
