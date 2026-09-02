# ---
# purpose: thread-safe done/total counter + stage log — the pipeline writes, the UI poll loop reads
# exports: ProgressState
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
