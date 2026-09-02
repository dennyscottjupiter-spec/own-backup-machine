# ---
# purpose: the USN-vs-walk decision ladder -> one VolumePlan per volume
# exports: build_plan(), compare_scanners_cli()
# depends: roots.py, models.VolumePlan, winapi.volumes.VolumeInfo
# gotcha: phase 1 is walk-only by design — the USN branch lands in phase 6, behind cfg.use_usn
# ---
from __future__ import annotations

from ..config import Config
from ..models import VolumePlan
from ..winapi.volumes import VolumeInfo
from . import roots


def build_plan(
    volumes: list[VolumeInfo],
    cfg: Config,
    cutoffs: dict[str, int] | None = None,
    cursors: dict[str, int] | None = None,
) -> list[VolumePlan]:
    cutoffs = cutoffs or {}
    cursors = cursors or {}
    roots_by_letter = roots.volume_roots(cfg, volumes)

    plans: list[VolumePlan] = []
    for v in volumes:
        vol_roots = roots_by_letter.get(v.letter)
        if not vol_roots:
            continue
        reason = "usn disabled in config" if not cfg.use_usn else "phase 1: walk-only build"
        plans.append(
            VolumePlan(
                letter=v.letter,
                guid_path=v.guid_path,
                fs_name=v.fs_name,
                method="walk",
                fallback_reason=reason,
                cursor=cursors.get(v.guid_path, 0),
                walk_cutoff_ns=cutoffs.get(v.guid_path, 0),
                roots=vol_roots,
            )
        )
    return plans


def compare_scanners_cli() -> int:
    print("--compare-scanners is implemented in phase 6 (USN journal work). Not available yet.")
    return 1
