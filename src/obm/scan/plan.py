# ---
# purpose: the USN-vs-walk decision ladder -> one VolumePlan per volume, plus --compare-scanners
# exports: build_plan(), compare_scanners_cli()
# depends: roots.py, usn_journal.py, state/cursors.py, models.VolumePlan, winapi.volumes.VolumeInfo,
#          humanize.py
# gotcha: do NOT pre-check elevation -- attempt the open and treat failure as "walk this volume";
#         IsUserAnAdmin() is only a status badge elsewhere, never a branch here
# ---
from __future__ import annotations

from .. import config as config_mod
from .. import humanize
from ..models import CandidateFile, VolumePlan
from ..state import cursors as cursors_mod
from ..state import store as state_store
from ..state.schema import VolumeState
from ..winapi import kernel32 as k32
from ..winapi import volumes as volumes_mod
from ..winapi.volumes import VolumeInfo
from . import roots, usn_journal
from .usn_scanner import scan as usn_scan
from .walk_scanner import scan as walk_scan


def _walk_plan(v: VolumeInfo, vol_roots: list[str], cutoff_ns: int, reason: str, cursor: int = 0) -> VolumePlan:
    return VolumePlan(
        letter=v.letter, guid_path=v.guid_path, fs_name=v.fs_name, method="walk",
        fallback_reason=reason, cursor=cursor, walk_cutoff_ns=cutoff_ns, roots=vol_roots,
    )


def _usn_or_walk_plan(v: VolumeInfo, vol_roots: list[str], cutoff_ns: int, stored: VolumeState | None) -> VolumePlan:
    try:
        handle = usn_journal.open_volume(v.letter)
    except OSError as e:
        return _walk_plan(v, vol_roots, cutoff_ns, f"cannot open volume: {e}")

    try:
        info = usn_journal.query_journal(handle)
    except OSError as e:
        return _walk_plan(v, vol_roots, cutoff_ns, f"journal query failed: {e}")
    finally:
        k32.CloseHandle(handle)

    method, reason = cursors_mod.decide(stored, info.journal_id, info.lowest_valid_usn, info.next_usn)
    if method == "walk":
        return _walk_plan(v, vol_roots, cutoff_ns, reason)

    return VolumePlan(
        letter=v.letter, guid_path=v.guid_path, fs_name=v.fs_name, method="usn",
        fallback_reason=reason, cursor=stored.next_usn, walk_cutoff_ns=cutoff_ns, roots=vol_roots,
    )


def build_plan(
    volumes: list[VolumeInfo],
    cfg: config_mod.Config,
    stored_states: dict[str, VolumeState] | None = None,
) -> list[VolumePlan]:
    stored_states = stored_states or {}
    roots_by_letter = roots.volume_roots(cfg, volumes)

    plans: list[VolumePlan] = []
    for v in volumes:
        vol_roots = roots_by_letter.get(v.letter)
        if not vol_roots:
            continue

        stored = stored_states.get(v.guid_path)
        cutoff_ns = cursors_mod.walk_cutoff_ns(stored)

        if not cfg.use_usn:
            plans.append(_walk_plan(v, vol_roots, cutoff_ns, "usn disabled in config"))
        elif not v.usn_capable:
            plans.append(_walk_plan(v, vol_roots, cutoff_ns, "volume not usn-capable"))
        else:
            plans.append(_usn_or_walk_plan(v, vol_roots, cutoff_ns, stored))

    return plans


def compare_scanners_cli() -> int:
    cfg = config_mod.load()
    app_state = state_store.load()
    vols = volumes_mod.list_volumes()

    exit_code = 0
    for v in vols:
        if not v.usn_capable:
            print(f"{v.letter}: not USN-capable, skipping")
            continue

        stored = app_state.volumes.get(v.guid_path)
        cutoff_ns = cursors_mod.walk_cutoff_ns(stored)
        vol_roots = roots.volume_roots(cfg, [v]).get(v.letter, [v.letter + "\\"])

        try:
            handle = usn_journal.open_volume(v.letter)
        except OSError as e:
            print(f"{v.letter}: cannot open volume ({e}), skipping")
            continue
        try:
            info = usn_journal.query_journal(handle)
        except OSError as e:
            print(f"{v.letter}: cannot query USN journal ({e}), skipping")
            continue
        finally:
            k32.CloseHandle(handle)

        start_usn = stored.next_usn if (stored and stored.journal_id == info.journal_id) else info.lowest_valid_usn

        walk_plan = _walk_plan(v, vol_roots, cutoff_ns, "compare")
        usn_plan = VolumePlan(
            letter=v.letter, guid_path=v.guid_path, fs_name=v.fs_name, method="usn",
            fallback_reason="compare", cursor=start_usn, walk_cutoff_ns=cutoff_ns, roots=vol_roots,
        )

        walk_paths = {c.path.lower() for c in walk_scan(walk_plan) if isinstance(c, CandidateFile)}
        usn_paths = {c.path.lower() for c in usn_scan(usn_plan) if isinstance(c, CandidateFile)}

        only_walk = walk_paths - usn_paths
        only_usn = usn_paths - walk_paths

        print(f"{v.letter}: walk={humanize.count(len(walk_paths))} usn={humanize.count(len(usn_paths))}")
        if only_walk or only_usn:
            exit_code = 1
            print(
                f"  MISMATCH: {humanize.count(len(only_walk))} only in walk, "
                f"{humanize.count(len(only_usn))} only in usn"
            )
            for p in list(only_walk)[:10]:
                print(f"    walk-only: {p}")
            for p in list(only_usn)[:10]:
                print(f"    usn-only: {p}")
        else:
            print("  MATCH")

    return exit_code
