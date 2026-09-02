# own-backup-machine

A Windows 11 backup tool that archives only the files changed since the last run, keeps the
original folder structure, automatically filters out junk, and — before copying anything — shows
a dark dashboard with charts and a treemap of exactly what is about to be backed up.

## Why

Delta-only backup engines already exist (restic, Kopia, rclone, Syncthing...). What this adds:

- **Automatic content-aware junk filtering** — a built-in blocklist (`node_modules`, build
  output, `AppData\Local\Temp`, `.git`, `thumbs.db`, ...) instead of hand-written exclude globs.
  Anything not recognized is **kept**, never silently dropped.
- **A dry-run visualization dashboard** — a squarified treemap and category charts of what a run
  would actually archive, before it touches anything.

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
Open it and set `[destination] path` to where backups should land, then use the **Settings**
button in the app (or edit the file directly) for everything else.

## CLI

```
python3 -m obm --doctor            # environment diagnostics: drives, elevation, archiver, destination
python3 -m obm --dry-run           # scan and report, no archive
python3 -m obm --run               # scan and archive now
python3 -m obm --compare-scanners  # diff USN vs walk results (elevated; the scan.use_usn release gate)
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
