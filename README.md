# own-backup-machine

A Windows 11 backup tool that looks at every file on the drive, archives the ones that are not
already in a backup, keeps the original folder structure, automatically filters out junk, and —
before copying anything — shows a dark dashboard with charts and a treemap of exactly what is
about to be backed up.

## Why

Delta-only backup engines already exist (restic, Kopia, rclone, Syncthing...). What this adds:

- **Every scan looks at every file** — the only thing that makes a file "already handled" is a
  fingerprint proving it went into an archive. A file you unticked, or one that was locked when
  a run happened, comes back in the next scan instead of disappearing because the clock moved on.
  `--reset-state` forgets those fingerprints and starts the baseline over.
- **Automatic content-aware junk filtering** — a built-in blocklist (`node_modules`, build
  output, `AppData\Local\Temp`, `.git`, `thumbs.db`, reinstallable binaries like `.exe`/`.dll`,
  VM and WSL disk images like `.vhdx`, ...) instead of hand-written exclude globs.
  Anything not recognized is **kept**, never silently dropped.
- **A dry-run visualization dashboard** — a squarified treemap and category charts of what a run
  would actually archive, before it touches anything, plus a "back up only these kinds"
  per-category selector in the Summary panel.
- **A destination picker in the run bar** — every writable drive (`X:`, `D:` and `E:` are always
  offered, even when unmapped) plus **Desktop** and **Downloads** (asked of Windows, so OneDrive
  redirection is handled) and a folder browser, saved back to `config.toml` the moment you pick one.
- **A dashboard you can resize** — drag the splitter between any two panels; the window size and
  every splitter position are restored on the next launch. `Esc` closes any popup window, and the
  Issues panel collapses to **one row per root folder** — biggest first, prefixed with `[size]` —
  so one noisy folder and its subfolders cannot bury everything else. Click a row to expand it.
- **A scan you can watch** — a centred strip under the title bar counts the files as they are
  found, names the folder being read, and shows a real percentage measured against how many files
  the previous scan walked past. No popup, nothing to dismiss.
- **A live run window** — an hourglass and a running log of exactly what the archive step is
  doing (lock check, compression, verification, copy, state commit). When it finishes, it opens
  the archive or its folder for you and names everything the run wrote. When it fails, a Copy
  button hands over the whole traceback — as does the one on the Issues panel.
- **Two indexes inside every archive** — `BACKUP-README.txt` at the archive root: how many files
  of which kinds, the folder tree with per-folder counts and sizes, and the full file list, so
  most archivers preview it inline and `grep` still works. Next to it, `BACKUP-README.html`: the
  same content as one offline page — a header card, a kind breakdown, a folder tree you can fold
  open with size bars, and a search box that filters rows as you type. No CDN, no network, no
  fonts to fetch. The file list on the page stops at 5,000 rows so a browser never chokes; the
  text file always has all of them. The same listing, plus every scan issue, is written next to
  the archive as `<archive-name>.manifest.json`.

## Requirements

- Windows 11, Python 3.11+ (developed against 3.14.3).
- `customtkinter==5.2.2` — installed automatically if you use `pyproject.toml`, or manually:
  ```
  python3 -m pip install customtkinter==5.2.2
  ```
- 7-Zip or WinRAR for compressed archives (optional — falls back to the stdlib `zipfile` module
  if neither is found).

## Running it

Double-click `run.bat`. That's it — no install step required; it sets `PYTHONPATH` itself.

- `run.bat` — normal launch. The scanner falls back to a full filesystem walk if the USN journal
  isn't usable (no elevation).
- `run-admin.bat` — self-elevating launch, needed only if you want the faster USN-journal scan
  path (`scan.use_usn = true` in `config.toml`).

First run creates `%LOCALAPPDATA%\own-backup-machine\config.toml` from `config.example.toml`.
Pick where backups land with the **Save to** dropdown in the run bar, and use the **Settings**
button in the app (or edit the file directly) for everything else.

## CLI

```
python3 -m obm --doctor            # environment diagnostics: drives, elevation, archiver, destination
python3 -m obm --dry-run           # scan and report, no archive
python3 -m obm --run               # scan and archive now
python3 -m obm --compare-scanners  # diff USN vs walk results (elevated; the scan.use_usn release gate)
python3 -m obm --reset-state       # forget what has been archived; the next run considers every file
python3 -m obm                     # GUI dashboard
```

## Development

```
python3 -m pip install -e .[dev]
python3 -m pytest
```

Every source file over 150 lines carries a `purpose` / `exports` / `depends` header comment at
the top — read that before the file body when getting oriented in `src/obm/`.

Before enabling `scan.use_usn`, work through `docs/manual-verification.md` on the real target
machine — it covers everything that can't be proven from an automated dev session (elevation,
OneDrive, a real NAS destination, a real multi-hundred-thousand-file `C:`).

## License

MIT — see `LICENSE`.
