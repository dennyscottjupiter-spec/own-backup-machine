# ---
# purpose: run a pipeline call on a background thread, hand the result back through a queue
# exports: Worker
# gotcha: Tkinter widgets are not thread-safe — the caller must poll(), never touch results
#         from inside the worker thread itself
# ---
from __future__ import annotations

import queue
import threading
from typing import Callable


class Worker:
    def __init__(self) -> None:
        self._queue: queue.Queue = queue.Queue()

    def submit(self, fn: Callable[[], object]) -> None:
        def _run() -> None:
            try:
                result = fn()
                self._queue.put(("ok", result))
            except Exception as e:  # surfaced to the UI thread, never raised here
                self._queue.put(("error", e))

        threading.Thread(target=_run, daemon=True).start()

    def poll(self) -> tuple[str, object] | None:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None
