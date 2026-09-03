# ---
# purpose: CLI entry point — --doctor|--dry-run|--run|--compare-scanners|--reset-state, else GUI
# depends: paths, config, logging_setup, winapi.volumes, archive.detect, state.reset
# ---
from __future__ import annotations

import argparse
import os
import sys

from . import config as config_mod
from . import paths
from .winapi import volumes


def _cmd_doctor() -> int:
    from .archive import detect

    print(f"config path : {paths.config_path()}")
    print(f"data dir    : {paths.data_dir()}")
    print(f"elevated    : {volumes.is_elevated()}")

    print("drives:")
    for v in volumes.list_volumes():
        journal = "usn-capable" if v.usn_capable else "walk-only"
        print(f"  {v.letter}  fs={v.fs_name:<8} type={v.drive_type}  {journal}  guid={v.guid_path}")

    tool = detect.detect()
    label = tool.exe_path or "stdlib zipfile"
    print(f"archiver    : {tool.name} ({label})")

    from .state.fingerprints import Fingerprints

    with Fingerprints() as fp:
        print(f"baseline    : {fp.count()} files already archived (--reset-state clears it)")

    cfg = config_mod.load()
    dest = cfg.destination_path
    if not dest:
        print("destination : not configured (edit config.toml)")
    else:
        reachable = os.path.isdir(dest) or os.path.isdir(os.path.dirname(dest) or dest)
        print(f"destination : {dest} ({'reachable' if reachable else 'NOT reachable'})")

    return 0


def _cmd_reset_state() -> int:
    from .state import reset

    removed = reset.reset()
    if not removed:
        print("nothing to reset -- no baseline files exist yet")
    for p in removed:
        print(f"removed {p}")
    print("the next run will consider every file on every configured volume again")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="obm")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--doctor", action="store_true", help="print environment diagnostics")
    group.add_argument("--dry-run", action="store_true", help="scan and report, no archive")
    group.add_argument("--run", action="store_true", help="scan, review is skipped, archive now")
    group.add_argument(
        "--compare-scanners", action="store_true", help="diff USN vs walk results"
    )
    group.add_argument(
        "--reset-state",
        action="store_true",
        help="forget what has been archived, so the next run considers every file again",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    from . import logging_setup

    logging_setup.setup()
    args = build_parser().parse_args(argv)

    if args.doctor:
        return _cmd_doctor()
    if args.dry_run:
        from .pipeline import dryrun

        return dryrun.run_cli()
    if args.run:
        from .pipeline import execute

        return execute.run_cli()
    if args.compare_scanners:
        from .scan import plan as plan_mod

        return plan_mod.compare_scanners_cli()
    if args.reset_state:
        return _cmd_reset_state()

    from .ui import window

    return window.run_gui()


if __name__ == "__main__":
    sys.exit(main())
