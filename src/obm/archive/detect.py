# ---
# purpose: locate 7-Zip / WinRAR: PATH -> standard install dirs -> registry, else stdlib zipfile
# exports: DetectedTool, detect()
# gotcha: WinRAR is commonly installed but NOT on PATH — PATH-only detection misses it
# ---
from __future__ import annotations

import shutil
import winreg
from dataclasses import dataclass
from pathlib import Path

_SEVENZIP_CANDIDATES = [
    r"C:\Program Files\7-Zip\7z.exe",
    r"C:\Program Files (x86)\7-Zip\7z.exe",
]
_WINRAR_CANDIDATES = [
    r"C:\Program Files\WinRAR\Rar.exe",
    r"C:\Program Files (x86)\WinRAR\Rar.exe",
]


@dataclass(slots=True)
class DetectedTool:
    name: str  # "7z" | "rar" | "zip"
    exe_path: str  # "" for the stdlib zip fallback


def _registry_dir(hive_key: str, value_name: str) -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, hive_key) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
    except OSError:
        return ""
    p = Path(value)
    return str(p if p.is_dir() else p.parent)


def _find_sevenzip() -> str:
    on_path = shutil.which("7z") or shutil.which("7z.exe")
    if on_path:
        return on_path
    for candidate in _SEVENZIP_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    reg_dir = _registry_dir(r"SOFTWARE\7-Zip", "Path")
    candidate = Path(reg_dir) / "7z.exe" if reg_dir else None
    return str(candidate) if candidate and candidate.is_file() else ""


def _find_winrar() -> str:
    on_path = shutil.which("Rar") or shutil.which("Rar.exe")
    if on_path:
        return on_path
    for candidate in _WINRAR_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    # "exe64" holds a full path to WinRAR.exe; Rar.exe (console tool) lives alongside it.
    reg_dir = _registry_dir(r"SOFTWARE\WinRAR", "exe64")
    candidate = Path(reg_dir) / "Rar.exe" if reg_dir else None
    return str(candidate) if candidate and candidate.is_file() else ""


def detect() -> DetectedTool:
    sevenzip = _find_sevenzip()
    if sevenzip:
        return DetectedTool(name="7z", exe_path=sevenzip)
    winrar = _find_winrar()
    if winrar:
        return DetectedTool(name="rar", exe_path=winrar)
    return DetectedTool(name="zip", exe_path="")
