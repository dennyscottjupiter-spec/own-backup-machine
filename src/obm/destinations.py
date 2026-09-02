# ---
# purpose: the drive roots an archive may be written to, plus the default destination choice
# exports: PREFERRED_DRIVE, drive_options(), resolve_default()
# depends: winapi/{constants,kernel32,volumes}
# gotcha: PREFERRED_DRIVE is offered even when absent -- a NAS letter is often mapped after boot
# ---
from __future__ import annotations

from .winapi import constants as c
from .winapi import kernel32 as k32
from .winapi.volumes import list_drive_letters

PREFERRED_DRIVE = "X:\\"

_WRITABLE_TYPES = (c.DRIVE_FIXED, c.DRIVE_REMOVABLE, c.DRIVE_REMOTE, c.DRIVE_RAMDISK)


def _drive_type(root: str) -> int:
    return k32.GetDriveTypeW(root)


def drive_options() -> list[str]:
    """Every writable drive root, preferred drive first."""
    roots = [
        letter + "\\"
        for letter in list_drive_letters()
        if _drive_type(letter + "\\") in _WRITABLE_TYPES
    ]
    return [PREFERRED_DRIVE] + [r for r in roots if r != PREFERRED_DRIVE]


def resolve_default(configured: str, options: list[str]) -> str:
    """A configured destination always wins -- the drive list is only the fallback."""
    if configured.strip():
        return configured.strip()
    return options[0] if options else ""
