# ---
# purpose: the Run button, its file/size caption, and a determinate archive-progress bar
# exports: RunBar
# depends: pipeline/selection.py
# ---
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import humanize
from ..models import DryRunResult
from ..pipeline.selection import selected_files
from . import theme


class RunBar(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk, on_run: Callable[[], None]) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)

        self.status_label = ctk.CTkLabel(self, text="Scan to begin", font=theme.body_font(), text_color=theme.MUTED)
        self.status_label.pack(side="left", padx=16, pady=10)

        self.progress_bar = ctk.CTkProgressBar(self, fg_color=theme.BG, progress_color=theme.ACCENT)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=16)

        self.run_button = ctk.CTkButton(self, text="Run", command=on_run, fg_color=theme.SUCCESS, state="disabled")
        self.run_button.pack(side="right", padx=16, pady=10)

    def update_result(self, result: DryRunResult) -> None:
        files = selected_files(result.candidates)
        total_bytes = sum(c.size for c in files)
        self.run_button.configure(text=f"Run — {len(files)} files, {humanize.size(total_bytes)}")

    def set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def set_progress(self, done: int, total: int) -> None:
        self.progress_bar.set(min(done / total, 1.0) if total > 0 else 0)

    def set_enabled(self, enabled: bool) -> None:
        self.run_button.configure(state="normal" if enabled else "disabled")
