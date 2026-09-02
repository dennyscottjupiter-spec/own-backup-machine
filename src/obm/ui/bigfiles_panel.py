# ---
# purpose: virtualized top-N big-file list with per-file checkboxes bound to CandidateFile.selected
# exports: BigFilesPanel
# gotcha: capped at MAX_SHOWN widgets regardless of how many big files exist -- this is the panel
#         half of the "no 100k widgets" freeze mitigation
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import humanize
from ..models import DryRunResult
from . import theme

MAX_SHOWN = 100


class BigFilesPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)

        heading = ctk.CTkLabel(self, text="Big files", font=theme.heading_font(), text_color=theme.TEXT)
        heading.pack(anchor="w", padx=16, pady=(12, 4))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def update_result(self, result: DryRunResult) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        big = sorted(
            (c for c in result.candidates if "big" in c.tags and c.verdict == "keep"),
            key=lambda c: c.size,
            reverse=True,
        )

        for c in big[:MAX_SHOWN]:
            var = ctk.BooleanVar(value=c.selected)

            def on_toggle(candidate=c, v=var) -> None:
                candidate.selected = v.get()

            row = ctk.CTkCheckBox(
                self.list_frame,
                text=f"{c.path}  ({humanize.size(c.size)})",
                variable=var,
                command=on_toggle,
                text_color=theme.TEXT,
                font=theme.body_font(11),
            )
            row.pack(fill="x", anchor="w", pady=1)

        if len(big) > MAX_SHOWN:
            more = ctk.CTkLabel(
                self.list_frame,
                text=f"+{len(big) - MAX_SHOWN} more big files not shown",
                text_color=theme.MUTED,
                font=theme.body_font(11),
            )
            more.pack(anchor="w", pady=(4, 0))
        elif not big:
            row = ctk.CTkLabel(self.list_frame, text="No big files", text_color=theme.MUTED, font=theme.body_font(11))
            row.pack(anchor="w")
