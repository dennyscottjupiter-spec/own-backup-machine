# ---
# purpose: load/save config.toml, seeding it from config.example.toml on first run
# exports: Config (dataclass), load(), save()
# depends: paths.py
# gotcha: save() hand-writes TOML (stdlib tomllib is read-only) -- literal '...' strings sidestep
#         backslash-escaping Windows paths
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


def _literal(s: str) -> str:
    return "'" + s.replace("'", "") + "'"


def _literal_list(items: list[str]) -> str:
    return "[" + ", ".join(_literal(i) for i in items) + "]"


def save(cfg: Config) -> None:
    paths.ensure_data_dir()
    text = (
        "[destination]\n"
        f"path = {_literal(cfg.destination_path)}\n\n"
        "[scan]\n"
        f"extra_roots = {_literal_list(cfg.extra_roots)}\n"
        f"extra_excludes = {_literal_list(cfg.extra_excludes)}\n"
        f"use_usn = {'true' if cfg.use_usn else 'false'}\n\n"
        "[archive]\n"
        f"level = {cfg.archive_level}\n"
        f"hash_max_mb = {cfg.hash_max_mb}\n\n"
        "[ui]\n"
        f"big_file_mb = {cfg.big_file_mb}\n"
    )
    paths.config_path().write_text(text, encoding="utf-8")
