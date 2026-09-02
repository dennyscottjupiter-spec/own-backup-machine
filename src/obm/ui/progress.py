# ---
# purpose: thread-safe done/total counter — the archive backend writes, the UI poll loop reads
# exports: ProgressState
# ---
from __future__ import annotations

import threading


class ProgressState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._done = 0
        self._total = 0

    def update(self, done: int, total: int) -> None:
        with self._lock:
            self._done = done
            self._total = total

    def snapshot(self) -> tuple[int, int]:
        with self._lock:
            return self._done, self._total
