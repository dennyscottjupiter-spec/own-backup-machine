# ---
# purpose: assemble the panels, own the worker-thread poll loop, wire scan/run to the pipeline
# exports: MainWindow, run_gui()
# depends: pipeline/{dryrun,execute}, ui/{worker,progress,topbar,summary_panel,bigfiles_panel,issues_panel,runbar}
# gotcha: only this file (plus worker.py) ever calls into pipeline/ -- everything else in ui/ is
#         presentation-only, which is what lets the UI ship with zero widget tests
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import config as config_mod
from ..pipeline import dryrun, execute
from . import theme
from .bigfiles_panel import BigFilesPanel
from .charts.treemap_view import TreemapPanel
from .history_panel import open_history_dialog
from .issues_panel import IssuesPanel
from .progress import ProgressState
from .runbar import RunBar
from .settings_dialog import open_settings_dialog
from .summary_panel import SummaryPanel
from .topbar import TopBar
from .worker import Worker


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        theme.apply()
        self.title("own-backup-machine")
        self.geometry("1200x750")
        self.configure(fg_color=theme.BG)

        self.cfg = config_mod.load()
        self.worker = Worker()
        self.result = None

        self.topbar = TopBar(
            self, on_scan=self.start_scan,
            on_history=lambda: open_history_dialog(self),
            on_settings=lambda: open_settings_dialog(self, self.cfg, self._on_settings_saved),
        )
        self.topbar.pack(fill="x", padx=12, pady=(12, 6))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=6)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.grid_rowconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self.summary_panel = SummaryPanel(left)
        self.summary_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

        self.bigfiles_panel = BigFilesPanel(left)
        self.bigfiles_panel.grid(row=1, column=0, sticky="nsew", pady=(0, 6))

        self.issues_panel = IssuesPanel(left)
        self.issues_panel.grid(row=2, column=0, sticky="nsew")

        self.treemap_panel = TreemapPanel(body)
        self.treemap_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.runbar = RunBar(self, on_run=self.start_run)
        self.runbar.pack(fill="x", padx=12, pady=(6, 12))

        self.start_scan()

    def _on_settings_saved(self, cfg: config_mod.Config) -> None:
        self.cfg = cfg
        self.start_scan()

    def start_scan(self) -> None:
        self.topbar.set_status("Scanning...")
        self.runbar.set_enabled(False)
        self.worker.submit(lambda: dryrun.run(self.cfg))
        self.after(100, self._poll_scan)

    def _poll_scan(self) -> None:
        item = self.worker.poll()
        if item is None:
            self.after(100, self._poll_scan)
            return
        kind, payload = item
        if kind == "error":
            self.topbar.set_status(f"Scan failed: {payload}")
            return
        self.result = payload
        self.summary_panel.update_result(self.result)
        self.bigfiles_panel.update_result(self.result)
        self.issues_panel.update_result(self.result)
        self.treemap_panel.update_result(self.result)
        self.runbar.update_result(self.result)
        self.topbar.set_status("Ready")
        self.runbar.set_enabled(True)

    def start_run(self) -> None:
        self.runbar.set_enabled(False)
        self.runbar.set_status("Archiving...")
        progress = ProgressState()
        self.worker.submit(lambda: execute.run(self.cfg, result=self.result, on_progress=progress.update))
        self.after(100, lambda: self._poll_run(progress))

    def _poll_run(self, progress: ProgressState) -> None:
        done, total = progress.snapshot()
        self.runbar.set_progress(done, total)

        item = self.worker.poll()
        if item is None:
            self.after(100, lambda: self._poll_run(progress))
            return

        kind, payload = item
        if kind == "error":
            self.runbar.set_status(f"Run failed: {payload}")
        else:
            self.runbar.set_status(f"Archived {payload.file_count} files -> {payload.archive_path}")
        self.runbar.set_progress(0, 0)
        self.runbar.set_enabled(True)


def run_gui() -> int:
    app = MainWindow()
    app.mainloop()
    return 0
