# ---
# purpose: the blocklist — pure data, auditable at a glance
# exports: BLOCKED_DIR_NAMES, BLOCKED_FILE_NAMES, BLOCKED_EXTENSIONS, BLOCKED_PATH_PATTERNS, CATEGORIES
# gotcha: an extension not in CATEGORIES is category "unknown" and is KEPT, never dropped
# ---
from __future__ import annotations

BLOCKED_DIR_NAMES = {
    "node_modules", "__pycache__", ".git", ".svn", "venv", ".venv", "env",
    "target", "build", "dist", "obj", "bin", ".gradle", ".next", ".nuxt", ".cache",
    ".pytest_cache", ".mypy_cache", ".tox", "vendor", "$recycle.bin",
    "system volume information", "windows", "program files", "program files (x86)", "programdata",
}

BLOCKED_FILE_NAMES = {
    "pagefile.sys", "hiberfil.sys", "swapfile.sys", "thumbs.db",
    "desktop.ini", ".ds_store", "ntuser.dat",
}

BLOCKED_EXTENSIONS = {
    ".log", ".tmp", ".temp", ".bak", ".old", ".pyc", ".pyo", ".o", ".obj",
    ".class", ".lock", ".crdownload", ".part", ".partial", ".dmp", ".etl",
}

BLOCKED_PATH_PATTERNS = (
    r"\\appdata\\local\\temp\\",
    r"\\appdata\\local\\.*cache.*\\",
    r"\\appdata\\roaming\\.*\\cache\\",
    r"\\appdata\\local\\packages\\.*\\localcache\\",
)

CATEGORIES = {  # display grouping ONLY — never causes a drop
    "document": {".docx", ".doc", ".odt", ".pdf", ".rtf", ".txt", ".md", ".pptx", ".ppt", ".xlsx", ".xls", ".csv", ".epub"},
    "photo": {".jpg", ".jpeg", ".png", ".heic", ".gif", ".tiff", ".webp", ".cr2", ".cr3", ".nef", ".arw", ".dng", ".psd", ".svg"},
    "video": {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm", ".m4v", ".mts"},
    "audio": {".mp3", ".flac", ".wav", ".m4a", ".aac", ".ogg", ".opus"},
    "code": {".py", ".js", ".ts", ".tsx", ".rs", ".go", ".java", ".c", ".cpp", ".h", ".cs", ".rb", ".php",
             ".sh", ".ps1", ".sql", ".html", ".css", ".json", ".yaml", ".yml", ".toml"},
    "archive": {".zip", ".7z", ".rar", ".tar", ".gz", ".iso"},
    "program": {".exe", ".msi", ".msix", ".appx", ".dll", ".sys", ".bat", ".cmd", ".com", ".jar", ".apk", ".deb"},
}
