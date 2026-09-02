# ---
# purpose: human-readable formatting for sizes, counts and durations
# exports: size(), count(), duration()
# ---
from __future__ import annotations

_UNITS = ("B", "KB", "MB", "GB", "TB")


def size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in _UNITS:
        if value < 1024.0 or unit == _UNITS[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} {_UNITS[-1]}"


def count(n: int) -> str:
    return f"{n:,}"


def duration(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"
