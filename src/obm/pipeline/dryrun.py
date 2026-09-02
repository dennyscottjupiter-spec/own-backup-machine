# ---
# purpose: scan every configured volume, score each candidate, no archiving — the --dry-run path
# exports: run(), run_cli()
# depends: scan/{plan,walk_scanner,issues}, filter/{matcher,classify}, pipeline/aggregate
# ---
from __future__ import annotations

import time

from .. import config as config_mod
from .. import humanize
from ..filter import classify, matcher
from ..models import CandidateFile, DryRunResult
from ..scan import confirm as confirm_mod
from ..scan import issues as issues_mod
from ..scan import plan as plan_mod
from ..scan import usn_scanner, walk_scanner
from ..state import carryover
from ..state import store as state_store
from ..state.fingerprints import Fingerprints
from ..winapi import volumes
from . import aggregate


def run(cfg: config_mod.Config) -> DryRunResult:
    vols = volumes.list_volumes()
    app_state = state_store.load()
    plans = plan_mod.build_plan(vols, cfg, stored_states=app_state.volumes)

    candidates: list[CandidateFile] = []
    all_issues = []
    with Fingerprints() as fp:
        for p in plans:
            scan_fn = usn_scanner.scan if p.method == "usn" else walk_scanner.scan
            for item in scan_fn(p):
                if isinstance(item, CandidateFile):
                    item.tags = classify.classify_tags(item.attributes, item.size, cfg.big_file_mb)
                    if confirm_mod.confirm(item, fp, cfg.hash_max_mb):
                        keep, rule = matcher.match(item.path, cfg.extra_excludes)
                        item.verdict = "keep" if keep else "drop"
                        item.drop_rule = rule
                    else:
                        item.verdict = "drop"
                        item.drop_rule = "unchanged-fingerprint"
                    candidates.append(item)
                else:
                    all_issues.append(item)

    for carried in carryover.to_candidates(carryover.load()):
        carried.tags = classify.classify_tags(
            carried.attributes, carried.size, cfg.big_file_mb, existing=carried.tags
        )
        carried.verdict = "keep"
        candidates.append(carried)

    return DryRunResult(candidates=candidates, issues=all_issues, plans=plans)


def run_cli() -> int:
    cfg = config_mod.load()
    started = time.time()
    result = run(cfg)
    elapsed = time.time() - started
    summary = aggregate.build_summary(result.candidates, result.issues)

    print(f"scanned {len(result.plans)} volume(s) in {humanize.duration(elapsed)}")
    print(f"keep : {humanize.count(summary.kept_count)} files, {humanize.size(summary.kept_bytes)}")
    print(f"drop : {humanize.count(summary.dropped_count)} files, {humanize.size(summary.dropped_bytes)}")
    print(f"cloud-only (skipped): {humanize.count(summary.placeholder_count)}")

    if summary.by_category:
        print("by category:")
        for cat, (count, total) in sorted(summary.by_category.items(), key=lambda kv: -kv[1][1]):
            print(f"  {cat:<10} {humanize.count(count):>9} files  {humanize.size(total)}")

    if summary.big_files:
        print(f"big files (>= {cfg.big_file_mb} MB): {humanize.count(len(summary.big_files))}")

    if result.issues:
        print("issues:")
        for kind, count in issues_mod.summarize(result.issues).items():
            print(f"  {issues_mod.KIND_LABELS.get(kind, kind)}: {humanize.count(count)}")

    return 0
