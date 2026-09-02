# ---
# purpose: config roots minus scan scope -> per-volume root list
# exports: is_under(), volume_roots()
# depends: config.Config, winapi.volumes.VolumeInfo
# gotcha: system dirs (Windows/Program Files/ProgramData) are pruned by filter.rules during the
#         walk itself, not here — default root is simply the whole drive
# ---
from __future__ import annotations

from pathlib import PureWindowsPath

from ..config import Config
from ..winapi.volumes import VolumeInfo


def is_under(path: str, root: str) -> bool:
    try:
        PureWindowsPath(path).relative_to(PureWindowsPath(root))
        return True
    except ValueError:
        return False


def volume_roots(cfg: Config, volumes: list[VolumeInfo]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {v.letter: [v.letter + "\\"] for v in volumes}

    for extra in cfg.extra_roots:
        letter = extra[:2].upper()
        if letter in result and extra not in result[letter]:
            result[letter].append(extra)

    return result
