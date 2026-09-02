---
title: Manual verification checklist (DESKTOP only)
status: current
updated: 2026-09-02
---

# Manual verification checklist

Everything on this list needs a live DESKTOP run to prove — none of it is exercisable from an
automated dev-notebook session (no elevation, no OneDrive-synced volume, no NAS drive letter, no
real 200k+ file `C:`). Tick each item off before trusting `scan.use_usn = true` or a full `--run`
against production data.

## Phase 0 — portability

- [ ] `--doctor` output on the dev-notebook and on DESKTOP diffed — nothing machine-specific
      leaked into the drive list, archiver detection, or destination reachability check.

## Phase 6 — USN journal (the release gate)

- [ ] `run-admin.bat` on DESKTOP, then `--doctor` shows `elevated: True` and every NTFS volume
      as `usn-capable`.
- [ ] Elevated `--compare-scanners` on the real `C:` — USN and walk result sets must be
      **identical**. Only flip `scan.use_usn = true` in `config.toml` once this is clean.
- [ ] `fsutil usn deletejournal /d C:` (elevated), then run again — the journal-recreated branch
      of `state/cursors.py`'s `decide()` must fire: a re-baseline walk, not a partial/missing
      result.

## Hard part 1 — OneDrive placeholders

- [ ] After a run over the OneDrive folder, free disk space is unchanged and no OneDrive sync
      activity was triggered (cloud-only files were listed and skipped, never hydrated).

## Hard part 6 — crash-safe archive write

- [ ] Map the NAS destination, start a `--run`, then `net use X: /delete` mid-archive — only a
      `.part` file and uncommitted state should remain; the next run must clean up the stale
      `.part` and retry cleanly.
- [ ] A genuine path over 260 characters is archived and restores correctly.

## Hard part 4 — carryover

- [ ] With a Word document open and a database engine running, start a `--run`. Both land in the
      carryover list (`locked`, via `pipeline/execute.py`'s `CreateFileW` pre-flight), and both
      are picked up automatically on the next run once closed.

## Performance, on the real dataset

- [ ] First run over the full `C:` — record wall-clock time and peak RSS. The 200k-file/<500ms
      treemap-layout benchmark (`tests/test_treemap_layout.py`) uses a synthetic tree; this is
      the real one.
- [ ] UI stays responsive scanning the real `C:` (100k+ files) — no freeze while the worker
      thread scans, lays out the treemap, or archives.
