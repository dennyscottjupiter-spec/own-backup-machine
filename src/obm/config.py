# ---
# purpose: load/save config.toml, seeding it from config.example.toml on first run
# exports: Config (dataclass), load()
# depends: paths.py
# ---
from __future__ import annotations

import shutil
import tomllib
from dataclasses import dataclass, field

from . import paths


@dataclass(slots=True)
class Config:
    destination_path: str = ""
    extra_roots: list[str] = field(default_factory=list)
    extra_excludes: list[str] = field(default_factory=list)
    use_usn: bool = False
    archive_level: int = 5
    hash_max_mb: int = 512
    big_file_mb: int = 100


def _seed_if_missing() -> None:
    dest = paths.config_path()
    if dest.exists():
        return
    paths.ensure_data_dir()
    template = paths.resource("config.example.toml")
    if template.exists():
        shutil.copyfile(template, dest)


def load() -> Config:
    _seed_if_missing()
    path = paths.config_path()
    if not path.exists():
        return Config()

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    dest = raw.get("destination", {})
    scan = raw.get("scan", {})
    archive = raw.get("archive", {})
    ui = raw.get("ui", {})

    return Config(
        destination_path=dest.get("path", ""),
        extra_roots=list(scan.get("extra_roots", [])),
        extra_excludes=list(scan.get("extra_excludes", [])),
        use_usn=bool(scan.get("use_usn", False)),
        archive_level=int(archive.get("level", 5)),
        hash_max_mb=int(archive.get("hash_max_mb", 512)),
        big_file_mb=int(ui.get("big_file_mb", 100)),
    )
