# ---
# purpose: resolve data/config/resource paths, frozen (PyInstaller) safe
# exports: data_dir(), config_path(), resource(), ensure_data_dir()
# gotcha: never touch __file__ anywhere else in the codebase
# ---
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "own-backup-machine"


def data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Local")
    return Path(base) / APP_NAME


def ensure_data_dir() -> Path:
    d = data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return data_dir() / "config.toml"


def _app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent.parent


def resource(*parts: str) -> Path:
    return _app_root().joinpath(*parts)
