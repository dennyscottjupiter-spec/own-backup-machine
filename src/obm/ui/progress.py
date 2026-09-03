# ---
# purpose: thread-safe counters the pipeline writes and the UI poll loop reads
# exports: ProgressState, ScanState
# ---
from __future__ import annotations

import threading


class ProgressState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._done = 0
        self._total = 0
        self._stages: list[str] = []

    def update(self, done: int, total: int) -> None:
        with self._lock:
            self._done = done
            self._total = total

    def stage(self, text: str) -> None:
        with self._lock:
            self._stages.append(text)

    def snapshot(self) -> tuple[int, int, list[str]]:
        with self._lock:
            return self._done, self._total, list(self._stages)


class ScanState:
    """Where a scan has got to. `expected` is the previous scan's total, so it can be 0."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._seen = 0
        self._expected = 0
        self._path = ""

    def update(self, seen: int, expected: int, path: str) -> None:
        with self._lock:
            self._seen = seen
            self._expected = expected
            self._path = path

    def snapshot(self) -> tuple[int, int, str]:
        with self._lock:
            return self._seen, self._expected, self._path
