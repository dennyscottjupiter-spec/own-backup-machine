# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Windows-only delta backup tool: scan what changed since the last run, filter out junk with a
built-in blocklist, show a dark CustomTkinter dashboard (treemap + charts) of what *would* be
archived, then archive it with 7-Zip / WinRAR / stdlib `zipfile`.

Pure stdlib except `customtkinter==5.2.2`. Win32 access is `ctypes` against `kernel32.dll` — no
`pywin32`.

## Commands

```powershell
python3 -m pytest                    # full suite (108 tests, <2s, no Windows privileges needed)
python3 -m pytest tests/test_confirm.py::test_name -q   # single test
python3 -m pip install -e .[dev]     # dev install (pyproject sets pythonpath=src, so tests run without it)

python3 -m obm --doctor              # drives, elevation, archiver, destination reachability
python3 -m obm --dry-run             # scan + report, archives nothing
python3 -m obm --run                 # scan + archive
python3 -m obm --compare-scanners    # USN vs walk diff (elevated) — the scan.use_usn release gate
python3 -m obm                       # GUI
```

`run.bat` / `run-admin.bat` are the user-facing launchers; they set `PYTHONPATH=src` themselves,
so there is no install step for running the app.

There is no linter or formatter configured. Don't add one.

## Read the file headers first

Every source file over ~150 lines starts with a `purpose` / `exports` / `depends` / `gotcha`
comment block. Reading those beats reading bodies when orienting — the `gotcha` lines encode
Win32/OneDrive/archiver traps that are expensive to rediscover. **A header must be updated in the
same edit that changes the file's exports or deps.**

## Architecture

Data flows one direction; every stage mutates the same `CandidateFile` records in place
(`models.py`, `slots=True` — this list can hold hundreds of thousands of entries, so new fields
have a real RAM cost).

```
winapi/  →  scan/  →  filter/  →  pipeline/  →  archive/ + state/
                                      ↑
                                     ui/  (only window.py and worker.py call into pipeline/)
```

- **`winapi/`** — ctypes layer. `kernel32.py` sets explicit `argtypes`/`restype` on everything;
  `volumes.py` identifies volumes by **GUID path, never drive letter**; `longpath.py` wraps every
  path in `\\?\` form before any file open.
- **`scan/`** — `plan.py` decides per volume whether to use the USN journal or a full walk, via the
  pure ladder in `state/cursors.py::decide()` (first run / journal recreated / wrapped / rewound →
  walk). `usn_scanner.py` and `walk_scanner.py` are interchangeable: both yield
  `CandidateFile | ScanIssue` from one `VolumePlan`. `confirm.py` drops false positives whose
  fingerprint is unchanged.
- **`filter/`** — `rules.py` is pure data (the blocklist). `matcher.py` checks **every ancestor
  directory name**, not just the leaf, so USN candidates (which never walk a directory tree) are
  judged identically to walked ones. An unrecognized extension is **kept**, never dropped.
- **`pipeline/`** — `dryrun.run()` produces the `DryRunResult` everything else consumes;
  `execute.run()` archives and then commits cursors + fingerprints + history + carryover as one
  unit, only after a verified write, narrating each step through its `on_stage` callback. `aggregate.py` is the read-only summary used by CLI and UI.
- **`archive/`** — three backends with an identical `create()`/`verify()` signature, chosen by
  `detect.py`. `writer.py` compresses to local disk, verifies, copies to the destination as
  `.part`, then `os.replace`s it.
- **`state/`** — JSON `store.py` (atomic tmp+replace) for cursors, sqlite `fingerprints.py` for
  archived-file identity, `carryover.py` for files that were locked/denied and must be reinjected
  next run regardless of cursor position.
- **`ui/`** — CustomTkinter. Scans and treemap layout run on a `Worker` thread and come back
  through a queue; Tk widgets are touched only from the Tk thread. `charts/squarify.py` and
  `charts/treemap_layout.py` are pure geometry with zero tkinter imports.
  `panel_header.py` builds every panel's title row, including the ⤢ Expand button that reopens
  that panel class full-size via `dialog.open_panel_window()`. `dialog.py` owns all Toplevel
  sizing, centring and raise-to-front — CustomTkinter's deferred internal update undoes a
  `lift()` issued at construction, so the raise **must** be re-issued from an `after()` callback.
  `type_filter.py` is the Summary panel's "back up only these kinds" selector: it writes
  `CandidateFile.selected` straight onto the shared records, so `window.py` redraws the Big files
  panel and the run bar from its `on_change` callback.
  `dest_picker.py` (in the run bar) offers every writable drive from `destinations.py` plus a
  folder browser, and `window.py` persists each pick to `config.toml` immediately.
  `run_dialog.py` + `hourglass.py` are the live run window: the pipeline's `on_stage` messages
  land in `ProgressState` and the poll loop replays them as a stage log.

### Invariants worth not breaking

- **Nothing outside `ui/` may import from `ui/`** — enforced by `tests/test_import_boundaries.py`.
  The one exemption is `__main__.py`, the composition root, which imports `ui/window.py` *inside*
  `main()` so a headless `--run` never imports tkinter.
- **Fixed strips are packed before the expanding body** in `ui/window.py`. The dashboard's natural
  height exceeds a laptop screen; a bar packed *after* an `expand=True` sibling finds an exhausted
  cavity and Tk leaves it **unmapped** — no error, just an invisible widget.
- **OneDrive placeholders are never archived** and never counted in kept bytes. `FILE_ATTRIBUTE_PINNED`
  means *locally present*, so it must not gate placeholder detection (`filter/classify.py`).
- **Never pre-check elevation before opening the USN journal** — attempt the open and treat failure
  as "walk this volume". Elevation is not the only reason it can fail.
- **The three archive backends stay signature-identical**, and their listfile encodings differ
  (7-Zip UTF-8 with `-scsUTF-8`, WinRAR UTF-16LE **with BOM**). Swapping them corrupts non-ASCII paths.
- `paths.py` is the only module allowed to touch `__file__` (PyInstaller-frozen safety).

## Verifying changes

Most of the interesting behavior cannot be proven on a dev machine: elevation, a real USN journal,
OneDrive placeholders, a NAS destination, a 200k-file `C:`. `docs/manual-verification.md` is the
checklist for what must be run on the real target machine — keep it current when adding behavior
that only shows up there, and don't claim a USN or destination path is verified from a dev session.

`scan.use_usn` stays `false` in `config.example.toml` until `--compare-scanners` has run clean on
the target machine.
