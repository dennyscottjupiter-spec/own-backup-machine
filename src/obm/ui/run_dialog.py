# ---
# purpose: the modal shown while a run archives -- hourglass, live stage log, progress, and an
#          outcome that either explains what was written and opens it, or is copyable
# exports: RunProgressDialog
# depends: archive/{manifest,readme}, ui/{hourglass,dialog,theme,open_path,copy_button}
# gotcha: the user may close this window mid-run (the run keeps going), so every update path
#         checks winfo_exists() before touching a widget. Auto-scrolling the stage log needs
#         CTkScrollableFrame's private _parent_canvas -- there is no public accessor in 5.2.2
# ---
from __future__ import annotations

import os
import time

import customtkinter as ctk

from ..archive.manifest import MANIFEST_SUFFIX
from ..archive.readme import README_NAME
from . import dialog, open_path, theme
from .copy_button import CopyButton
from .hourglass import Hourglass

WHAT_ELSE_WAS_WRITTEN = (
    "Also written, so you never have to open the archive to see what is in it:\n"
    "  • {manifest}  — next to the archive: every file and every issue of this run, as JSON.\n"
    "  • {readme}  — inside the archive: the folder structure and the full file list, plain text."
)


class RunProgressDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master)
        self.title("Backing up")
        self.configure(fg_color=theme.BG)
        self._started = time.monotonic()
        self._shown = 0
        self._rows: list[ctk.CTkLabel] = []
        self._finished = False

        head = ctk.CTkFrame(self, fg_color=theme.PANEL_BG, corner_radius=8)
        head.pack(fill="x", padx=12, pady=(12, 6))

        self.hourglass = Hourglass(head)
        self.hourglass.pack(side="left", padx=(16, 12), pady=12)
        self.hourglass.start()

        text_col = ctk.CTkFrame(head, fg_color="transparent")
        text_col.pack(side="left", fill="both", expand=True, pady=12)
        self.headline = ctk.CTkLabel(
            text_col, text="Starting...", font=theme.heading_font(15), text_color=theme.TEXT, anchor="w"
        )
        self.headline.pack(fill="x")
        self.elapsed_label = ctk.CTkLabel(
            text_col, text="0s elapsed", font=theme.body_font(11), text_color=theme.MUTED, anchor="w"
        )
        self.elapsed_label.pack(fill="x", pady=(2, 0))

        self.progress_bar = ctk.CTkProgressBar(self, fg_color=theme.PANEL_BG, progress_color=theme.ACCENT)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=12)

        self.log = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL_BG, corner_radius=8)

        self.close_button = ctk.CTkButton(self, text="Close", command=self.destroy, fg_color=theme.PANEL_BG)
        self.close_button.pack(side="bottom", pady=(0, 12))
        # packed before the log so the packer reserves its strip: a bar packed after an
        # expand=True sibling finds an exhausted cavity and Tk leaves it unmapped
        self.actions = ctk.CTkFrame(self, fg_color="transparent")
        self.actions.pack(side="bottom", fill="x", padx=12, pady=(0, 6))
        self.log.pack(fill="both", expand=True, padx=12, pady=6)

        dialog.place_over(self, master, 620, 520)
        self._tick_elapsed()

    def update_progress(self, done: int, total: int, stages: list[str]) -> None:
        if not self.winfo_exists():
            return
        self.progress_bar.set(min(done / total, 1.0) if total > 0 else 0)
        for stage in stages[self._shown:]:
            for row in self._rows:
                row.configure(text="✓ " + row.cget("text")[2:], text_color=theme.MUTED)
            row = ctk.CTkLabel(
                self.log, text="▸ " + stage, font=theme.body_font(12), text_color=theme.TEXT, anchor="w"
            )
            row.pack(fill="x", anchor="w", pady=1)
            self._rows.append(row)
            self.headline.configure(text=stage)
        if len(stages) > self._shown:
            self._scroll_to_end()
        self._shown = len(stages)

    def _scroll_to_end(self) -> None:
        self.log.update_idletasks()
        self.log._parent_canvas.yview_moveto(1.0)

    def finish(self, text: str, ok: bool = True, archive_path: str = "", detail: str = "") -> None:
        self._finished = True
        if not self.winfo_exists():
            return
        self.hourglass.stop()
        for row in self._rows:
            row.configure(text="✓ " + row.cget("text")[2:], text_color=theme.MUTED)
        self.headline.configure(text="Done" if ok else "Failed", text_color=theme.SUCCESS if ok else theme.DANGER)
        outcome = ctk.CTkLabel(
            self.log, text=text, font=theme.body_font(12), wraplength=520,
            text_color=theme.SUCCESS if ok else theme.DANGER, anchor="w", justify="left",
        )
        outcome.pack(fill="x", anchor="w", pady=(6, 1))
        if archive_path:
            self._explain_sidecars(archive_path)
            self._add_open_buttons(archive_path)
        if not ok:
            CopyButton(self.actions, lambda: f"{text}\n\n{detail}" if detail else text).pack(side="right")
        self._scroll_to_end()
        self.progress_bar.set(1.0 if ok else 0)
        self.close_button.configure(fg_color=theme.ACCENT)

    def _explain_sidecars(self, archive_path: str) -> None:
        """Nobody should discover the manifest by accident -- say what a run wrote, and where."""
        ctk.CTkLabel(
            self.log,
            text=WHAT_ELSE_WAS_WRITTEN.format(
                manifest=os.path.basename(archive_path) + MANIFEST_SUFFIX, readme=README_NAME
            ),
            font=theme.body_font(11), wraplength=520, text_color=theme.MUTED,
            anchor="w", justify="left",
        ).pack(fill="x", anchor="w", pady=(8, 1))

    def _add_open_buttons(self, archive_path: str) -> None:
        ctk.CTkButton(
            self.actions, text="📂 Open folder", width=140, fg_color=theme.PANEL_BG,
            command=lambda: open_path.open_containing_folder(archive_path),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            self.actions, text="📦 Open archive", width=140, fg_color=theme.PANEL_BG,
            command=lambda: open_path.open_file(archive_path),
        ).pack(side="left")

    def _tick_elapsed(self) -> None:
        if self._finished or not self.winfo_exists():
            return
        self.elapsed_label.configure(text=f"{int(time.monotonic() - self._started)}s elapsed")
        self.after(500, self._tick_elapsed)
