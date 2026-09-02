# ---
# purpose: enumerate fixed/removable drives with filesystem + USN capability + elevation badge
# exports: VolumeInfo, list_volumes(), is_elevated()
# depends: kernel32.py, constants.py
# gotcha: DRIVE_REMOTE never has a journal; letters are unstable, GUID path is the real identity
# ---
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass

from . import constants as c
from . import kernel32 as k32


@dataclass(slots=True)
class VolumeInfo:
    letter: str  # "C:"
    drive_type: int
    fs_name: str
    usn_capable: bool
    guid_path: str


def is_elevated() -> bool:
    try:
        return bool(k32.IsUserAnAdmin())
    except OSError:
        return False


def list_drive_letters() -> list[str]:
    buf = ctypes.create_unicode_buffer(1024)
    n = k32.GetLogicalDriveStringsW(len(buf), buf)
    if n == 0:
        return []
    raw = buf[:n]
    return [seg.rstrip("\\") for seg in raw.split("\x00") if seg]


def _volume_information(root: str) -> tuple[str, int] | None:
    fs_name_buf = ctypes.create_unicode_buffer(261)
    flags = wintypes.DWORD(0)
    ok = k32.GetVolumeInformationW(
        root,
        None,
        0,
        None,
        None,
        ctypes.byref(flags),
        fs_name_buf,
        len(fs_name_buf),
    )
    if not ok:
        return None
    return fs_name_buf.value, flags.value


def _guid_path(root: str) -> str:
    buf = ctypes.create_unicode_buffer(260)
    ok = k32.GetVolumeNameForVolumeMountPointW(root, buf, len(buf))
    return buf.value if ok else ""


def list_volumes() -> list[VolumeInfo]:
    volumes: list[VolumeInfo] = []
    for letter in list_drive_letters():
        root = letter + "\\"
        drive_type = k32.GetDriveTypeW(root)
        if drive_type not in (c.DRIVE_FIXED, c.DRIVE_REMOVABLE):
            continue
        info = _volume_information(root)
        if info is None:
            continue
        fs_name, flags = info
        usn_capable = (
            fs_name.upper() == "NTFS" and bool(flags & c.FILE_SUPPORTS_USN_JOURNAL)
        )
        volumes.append(
            VolumeInfo(
                letter=letter,
                drive_type=drive_type,
                fs_name=fs_name,
                usn_capable=usn_capable,
                guid_path=_guid_path(root),
            )
        )
    return volumes
