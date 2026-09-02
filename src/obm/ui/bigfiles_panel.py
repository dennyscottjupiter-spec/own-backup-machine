# ---
# purpose: virtualized top-N big-file list with per-file checkboxes bound to CandidateFile.selected
# exports: BigFilesPanel
# depends: ui/panel_header.py, humanize.py
# gotcha: capped at max_shown widgets regardless of how many big files exist -- this is the panel
#         half of the "no 100k widgets" freeze mitigation. Select all / none therefore acts on the
#         FULL big-file list, not only on the rows that happen to have a checkbox on screen.
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import humanize
from ..models import DryRunResult
from . import panel_header, theme

MAX_SHOWN = 100


class BigFilesPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, on_expand=None, max_shown: int = MAX_SHOWN) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)
        self._max_shown = max_shown
        self._big: list = []
        self._vars: list = []

        header = panel_header.build(self, "Big files", on_expand)
        ctk.CTkButton(
            header, text="None", width=54, height=24, fg_color=theme.BG,
            font=theme.body_font(11), command=lambda: self._set_all(False),
        ).pack(side="right", padx=(4, 8))
        ctk.CTkButton(
            header, text="Select all", width=76, height=24, fg_color=theme.ACCENT,
            font=theme.body_font(11), command=lambda: self._set_all(True),
        ).pack(side="right", padx=4)

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def _set_all(self, selected: bool) -> None:
        for c in self._big:
            c.selected = selected
        for var in self._vars:
            var.set(selected)

    def update_result(self, result: DryRunResult) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        self._vars = []

        self._big = sorted(
            (c for c in result.candidates if "big" in c.tags and c.verdict == "keep"),
            key=lambda c: c.size,
            reverse=True,
        )

        for c in self._big[: self._max_shown]:
            var = ctk.BooleanVar(value=c.selected)
            self._vars.append(var)

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

        hidden = len(self._big) - self._max_shown
        if hidden > 0:
            more = ctk.CTkLabel(
                self.list_frame,
                text=f"+{humanize.count(hidden)} more big files not shown",
                text_color=theme.MUTED,
                font=theme.body_font(11),
            )
            more.pack(anchor="w", pady=(4, 0))
        elif not self._big:
            row = ctk.CTkLabel(self.list_frame, text="No big files", text_color=theme.MUTED, font=theme.body_font(11))
            row.pack(anchor="w")
