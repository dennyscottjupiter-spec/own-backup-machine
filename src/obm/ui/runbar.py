# ---
# purpose: the Run button, its file/size caption, the destination picker, a progress bar, and the
#          failure line with the Copy button that makes it pasteable
# exports: RunBar
# depends: pipeline/selection.py, ui/{dest_picker,copy_button}
# gotcha: the Copy button is packed only while a failure is showing -- an always-present one on a
#         bar that is almost always fine would just be noise
# ---
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import humanize
from ..models import DryRunResult
from ..pipeline.selection import selected_files
from . import theme
from .copy_button import CopyButton
from .dest_picker import DestPicker


class RunBar(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk,
        on_run: Callable[[], None],
        destination: str = "",
        on_destination_change: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)

        self._detail = ""
        self.status_label = ctk.CTkLabel(self, text="Scan to begin", font=theme.body_font(), text_color=theme.MUTED)
        self.status_label.pack(side="left", padx=16, pady=10)
        self.copy_button = CopyButton(self, lambda: self._detail)

        self.progress_bar = ctk.CTkProgressBar(self, fg_color=theme.BG, progress_color=theme.ACCENT)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=16)

        self.run_button = ctk.CTkButton(self, text="Run", command=on_run, fg_color=theme.SUCCESS, state="disabled")
        self.run_button.pack(side="right", padx=16, pady=10)

        # packed after the Run button so it lands to its left
        self.dest_picker = DestPicker(self, destination, on_destination_change)
        self.dest_picker.pack(side="right", padx=8, pady=10)

    def destination(self) -> str:
        return self.dest_picker.get()

    def update_result(self, result: DryRunResult) -> None:
        files = selected_files(result.candidates)
        total_bytes = sum(c.size for c in files)
        self.run_button.configure(text=f"Run — {humanize.count(len(files))} files, {humanize.size(total_bytes)}")

    def set_status(self, text: str, detail: str = "") -> None:
        """`detail` marks the line as a failure: it turns red and grows a Copy button that hands
        over the full traceback, so a bug report is one click instead of a retyped screenshot."""
        self.status_label.configure(text=text, text_color=theme.DANGER if detail else theme.MUTED)
        self._detail = f"{text}\n\n{detail}" if detail else ""
        if detail:
            # before= is not cosmetic: packed last it would sit after the expand=True progress bar,
            # find an exhausted cavity, and Tk would silently leave it unmapped
            self.copy_button.pack(side="left", pady=10, before=self.progress_bar)
        else:
            self.copy_button.pack_forget()

    def set_progress(self, done: int, total: int) -> None:
        self.progress_bar.set(min(done / total, 1.0) if total > 0 else 0)

    def set_enabled(self, enabled: bool) -> None:
        self.run_button.configure(state="normal" if enabled else "disabled")
