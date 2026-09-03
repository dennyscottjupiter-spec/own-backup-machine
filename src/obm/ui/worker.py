# ---
# purpose: run a pipeline call on a background thread, hand the result back through a queue
# exports: WorkerError, Worker
# gotcha: Tkinter widgets are not thread-safe — the caller must poll(), never touch results
#         from inside the worker thread itself. The traceback is formatted here, in the thread
#         that still has the live exception — it cannot be recovered on the UI side later.
# ---
from __future__ import annotations

import queue
import threading
import traceback
from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True)
class WorkerError:
    message: str  # the one-liner the status bar shows
    detail: str  # the full traceback, for the Copy button


class Worker:
    def __init__(self) -> None:
        self._queue: queue.Queue = queue.Queue()

    def submit(self, fn: Callable[[], object]) -> None:
        def _run() -> None:
            try:
                result = fn()
                self._queue.put(("ok", result))
            except Exception as e:  # surfaced to the UI thread, never raised here
                self._queue.put((
                    "error",
                    WorkerError(message=f"{type(e).__name__}: {e}", detail=traceback.format_exc()),
                ))

        threading.Thread(target=_run, daemon=True).start()

    def poll(self) -> tuple[str, object] | None:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None
