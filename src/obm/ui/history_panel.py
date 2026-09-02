# ---
# purpose: browse past runs and delete their archives -- state/history.py has no UI of its own
# exports: open_history_dialog()
# depends: state/history.py, humanize.py, ui/dialog.py
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import humanize
from ..models import RunRecord
from ..state import history
from . import dialog, theme


class HistoryDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master)
        self.title("Run history")
        self.configure(fg_color=theme.BG)

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=12)
        self._refresh()
        dialog.place_over(self, master, 640, 420)

    def _refresh(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        records = list(reversed(history.load()))
        if not records:
            ctk.CTkLabel(self.list_frame, text="No runs yet", text_color=theme.MUTED).pack(anchor="w")
            return

        for record in records:
            self._add_row(record)

    def _add_row(self, record: RunRecord) -> None:
        row = ctk.CTkFrame(self.list_frame, fg_color=theme.PANEL_BG, corner_radius=6)
        row.pack(fill="x", pady=4)

        text = (
            f"{record.started_utc}  —  {record.status}\n"
            f"{humanize.count(record.file_count)} files, {humanize.size(record.total_bytes)}\n"
            f"{record.archive_path}"
        )
        ctk.CTkLabel(
            row, text=text, text_color=theme.TEXT, font=theme.body_font(11), justify="left", anchor="w"
        ).pack(side="left", padx=10, pady=8, fill="x", expand=True)

        ctk.CTkButton(
            row, text="Delete", width=70, fg_color=theme.DANGER, command=lambda r=record: self._delete(r)
        ).pack(side="right", padx=10)

    def _delete(self, record: RunRecord) -> None:
        history.delete(record.run_id)
        self._refresh()


def open_history_dialog(master: ctk.CTk) -> None:
    HistoryDialog(master)
