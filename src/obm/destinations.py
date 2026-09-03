# ---
# purpose: the drive roots and folders an archive may be written to, plus the default choice
# exports: PREFERRED_DRIVE, ALWAYS_OFFERED, drive_options(), folder_options(),
#          destination_options(), resolve_default()
# depends: winapi/{constants,kernel32,volumes,knownfolders}
# gotcha: ALWAYS_OFFERED drives are listed even when absent or of an unwritable type -- a NAS
#         letter is often mapped after boot, and D:/E: are this machine's usual backup disks.
#         Desktop/Downloads come from SHGetKnownFolderPath, never from %USERPROFILE% -- OneDrive
#         redirects them -- and drop out of the list entirely if Windows cannot resolve them
# ---
from __future__ import annotations

import os

from .winapi import constants as c
from .winapi import kernel32 as k32
from .winapi.knownfolders import DESKTOP, DOWNLOADS, known_folder
from .winapi.volumes import list_drive_letters

PREFERRED_DRIVE = "X:\\"
ALWAYS_OFFERED = (PREFERRED_DRIVE, "D:\\", "E:\\")

_WRITABLE_TYPES = (c.DRIVE_FIXED, c.DRIVE_REMOVABLE, c.DRIVE_REMOTE, c.DRIVE_RAMDISK)


def _drive_type(root: str) -> int:
    return k32.GetDriveTypeW(root)


def drive_options() -> list[str]:
    """Every writable drive root, the always-offered drives first."""
    roots = [
        letter + "\\"
        for letter in list_drive_letters()
        if _drive_type(letter + "\\") in _WRITABLE_TYPES
    ]
    return list(ALWAYS_OFFERED) + [r for r in roots if r not in ALWAYS_OFFERED]


def folder_options() -> list[str]:
    """Desktop and Downloads -- the two folders people actually go looking in afterwards."""
    return [path for path in (known_folder(DESKTOP), known_folder(DOWNLOADS)) if path and os.path.isdir(path)]


def destination_options() -> list[str]:
    """Everything the Save to picker offers: drives first, then the two well-known folders."""
    drives = drive_options()
    return drives + [f for f in folder_options() if f not in drives]


def resolve_default(configured: str, options: list[str]) -> str:
    """A configured destination always wins -- the drive list is only the fallback."""
    if configured.strip():
        return configured.strip()
    return options[0] if options else ""
