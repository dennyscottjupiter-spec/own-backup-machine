# ---
# purpose: assemble the panels into resizable panes, own the worker-thread poll loop, wire
#          scan/run to the pipeline, and persist the window geometry + sash positions on close
# exports: MainWindow, run_gui()
# depends: pipeline/{dryrun,execute}, config.py, ui/{worker,progress,topbar,summary_panel,
#          bigfiles_panel,issues_panel,runbar,run_dialog,dialog,layout}
# gotcha: only this file (plus worker.py) ever calls into pipeline/ -- everything else in ui/ is
#         presentation-only, which is what lets the UI ship with zero widget tests.
#         Closing goes through _on_close (WM_DELETE_WINDOW), so the layout is only saved on a real
#         window close -- a killed process keeps the previous layout.
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import config as config_mod
from .. import humanize
from ..pipeline import dryrun, execute
from . import dialog, layout, theme
from .bigfiles_panel import BigFilesPanel
from .charts.treemap_view import TreemapPanel
from .history_panel import open_history_dialog
from .issues_panel import IssuesPanel
from .progress import ProgressState
from .run_dialog import RunProgressDialog
from .runbar import RunBar
from .settings_dialog import open_settings_dialog
from .summary_panel import SummaryPanel
from .topbar import TopBar
from .worker import Worker

# the dashboard tiles stay capped at 100 rows; the popped-out copy can afford more widgets
DETAIL_MAX_SHOWN = 500

DEFAULT_GEOMETRY = "1200x750"
PANEL_MIN_W = 260
PANEL_MIN_H = 90
RESTORE_DELAY_MS = 200


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        theme.apply()
        self.title("own-backup-machine")
        self.configure(fg_color=theme.BG)

        self.cfg = config_mod.load()
        self.geometry(self.cfg.layout_geometry or DEFAULT_GEOMETRY)
        self.worker = Worker()
        self.result = None

        self.topbar = TopBar(
            self, on_scan=self.start_scan,
            on_history=lambda: open_history_dialog(self),
            on_settings=lambda: open_settings_dialog(self, self.cfg, self._on_settings_saved),
        )
        self.topbar.pack(fill="x", padx=12, pady=(12, 6))

        # packed before the body so the packer reserves its strip first: the body's natural
        # height exceeds any laptop screen, and a bar packed after it is silently left unmapped
        self.runbar = RunBar(
            self, on_run=self.start_run,
            destination=self.cfg.destination_path,
            on_destination_change=self._on_destination_change,
        )
        self.runbar.pack(side="bottom", fill="x", padx=12, pady=(6, 12))
        # an unset destination resolves to the preferred drive -- persist that as the real choice
        if self.runbar.destination() != self.cfg.destination_path:
            self._on_destination_change(self.runbar.destination())

        # every divider is a draggable sash: the panels are what the user resizes, and where they
        # leave them is written back to config.toml on close
        self.body = layout.make_paned(self, "horizontal")
        self.body.pack(fill="both", expand=True, padx=12, pady=6)

        self.left = layout.make_paned(self.body, "vertical")

        self.summary_panel = SummaryPanel(
            self.left,
            on_expand=lambda: self._expand("Summary", SummaryPanel),
            on_selection_change=self._on_selection_change,
        )
        self.bigfiles_panel = BigFilesPanel(
            self.left,
            on_expand=lambda: self._expand("Big files", lambda m: BigFilesPanel(m, max_shown=DETAIL_MAX_SHOWN)),
        )
        self.issues_panel = IssuesPanel(
            self.left,
            on_expand=lambda: self._expand("Issues", lambda m: IssuesPanel(m, max_shown=DETAIL_MAX_SHOWN)),
        )
        # Summary scrolls internally, so it opens taller than the two list panels below it
        self.left.add(self.summary_panel, stretch="never", height=320, minsize=PANEL_MIN_H)
        self.left.add(self.bigfiles_panel, stretch="always", minsize=PANEL_MIN_H)
        self.left.add(self.issues_panel, stretch="always", minsize=PANEL_MIN_H)

        self.treemap_panel = TreemapPanel(self.body, on_expand=lambda: self._expand("Treemap", TreemapPanel))
        self.body.add(self.left, stretch="always", width=420, minsize=PANEL_MIN_W)
        self.body.add(self.treemap_panel, stretch="always", minsize=PANEL_MIN_W)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(RESTORE_DELAY_MS, self._restore_layout)

        self.start_scan()

    def _restore_layout(self) -> None:
        self.update_idletasks()
        layout.apply_sashes(self.body, self.cfg.layout_main_sashes)
        layout.apply_sashes(self.left, self.cfg.layout_left_sashes)

    def _on_close(self) -> None:
        self.cfg.layout_geometry = self.geometry()
        self.cfg.layout_main_sashes = layout.read_sashes(self.body)
        self.cfg.layout_left_sashes = layout.read_sashes(self.left)
        config_mod.save(self.cfg)
        self.destroy()

    def _on_selection_change(self) -> None:
        # the type filter mutates CandidateFile.selected directly, so the panels bound to those
        # same records have to be redrawn from their current state
        if self.result is None:
            return
        self.bigfiles_panel.update_result(self.result)
        self.runbar.update_result(self.result)

    def _expand(self, title: str, factory) -> None:
        dialog.open_panel_window(self, title, factory, self.result)

    def _on_destination_change(self, path: str) -> None:
        self.cfg.destination_path = path
        config_mod.save(self.cfg)

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
        self.run_dialog = RunProgressDialog(self)
        self.worker.submit(
            lambda: execute.run(
                self.cfg, result=self.result, on_progress=progress.update, on_stage=progress.stage
            )
        )
        self.after(100, lambda: self._poll_run(progress))

    def _poll_run(self, progress: ProgressState) -> None:
        done, total, stages = progress.snapshot()
        self.runbar.set_progress(done, total)
        self.run_dialog.update_progress(done, total, stages)

        item = self.worker.poll()
        if item is None:
            self.after(100, lambda: self._poll_run(progress))
            return

        kind, payload = item
        if kind == "error":
            message = f"Run failed: {payload}"
        else:
            message = f"Archived {humanize.count(payload.file_count)} files -> {payload.archive_path}"
        self.runbar.set_status(message)
        self.run_dialog.finish(message, ok=kind != "error")
        self.runbar.set_progress(0, 0)
        self.runbar.set_enabled(True)


def run_gui() -> int:
    app = MainWindow()
    app.mainloop()
    return 0
