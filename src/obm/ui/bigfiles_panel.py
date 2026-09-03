# ---
# purpose: virtualized top-N big-file list with per-file checkboxes bound to CandidateFile.selected,
#          kept in step with whatever the Summary type filter last did to those same records
# exports: BigFilesPanel
# depends: ui/panel_header.py, humanize.py
# gotcha: capped at max_shown widgets regardless of how many big files exist -- this is the panel
#         half of the "no 100k widgets" freeze mitigation. The select toggle therefore acts on the
#         FULL big-file list, not only on the rows that happen to have a checkbox on screen.
#         refresh_selection() re-reads the records into the existing rows and must NEVER rebuild
#         them: it is reachable from a checkbox command, and a rebuild there destroys the widget
#         that fired it mid-click.
# ---
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import humanize
from ..models import CandidateFile, DryRunResult
from . import panel_header, theme

MAX_SHOWN = 100
SELECT_ALL = "Select all"
SELECT_NONE = "Select none"


class BigFilesPanel(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_expand=None,
        max_shown: int = MAX_SHOWN,
        on_selection_change: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)
        self._max_shown = max_shown
        self._on_selection_change = on_selection_change
        self._big: list[CandidateFile] = []
        self._rows: list[tuple[CandidateFile, ctk.BooleanVar, ctk.CTkCheckBox]] = []
        self._all_selected = False

        header = panel_header.build(self, "Big files", on_expand)
        self.select_button = ctk.CTkButton(
            header, text=SELECT_ALL, width=88, height=24, fg_color=theme.ACCENT,
            font=theme.body_font(11), command=self._toggle_all,
        )
        self.select_button.pack(side="right", padx=(4, 8))
        self.count_label = ctk.CTkLabel(header, text="", font=theme.body_font(11), text_color=theme.MUTED)
        self.count_label.pack(side="right", padx=8)

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def _toggle_all(self) -> None:
        """One button: first press selects everything, the next press clears it again."""
        self._set_all(not self._all_selected)

    def _set_all(self, selected: bool) -> None:
        for c in self._big:
            c.selected = selected
        self._sync_rows()
        self._notify()

    def _notify(self) -> None:
        if self._on_selection_change is not None:
            self._on_selection_change()

    def refresh_selection(self) -> None:
        """The Summary type filter (or Select all) rewrote these same records -- show it."""
        self._sync_rows()

    def _sync_rows(self) -> None:
        """Re-read CandidateFile.selected into the live widgets. No widget is created or destroyed
        here, which is what makes it safe to call from a checkbox command."""
        for c, var, box in self._rows:
            var.set(c.selected)
            box.configure(text_color=theme.TEXT if c.selected else theme.MUTED)

        picked = sum(1 for c in self._big if c.selected)
        self._all_selected = bool(self._big) and picked == len(self._big)
        self.select_button.configure(text=SELECT_NONE if self._all_selected else SELECT_ALL)
        self.count_label.configure(
            text=f"{humanize.count(picked)} of {humanize.count(len(self._big))} selected" if self._big else ""
        )

    def update_result(self, result: DryRunResult) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        self._rows = []

        self._big = sorted(
            (c for c in result.candidates if "big" in c.tags and c.verdict == "keep"),
            key=lambda c: c.size,
            reverse=True,
        )

        for c in self._big[: self._max_shown]:
            var = ctk.BooleanVar(value=c.selected)

            def on_toggle(candidate=c, v=var) -> None:
                candidate.selected = v.get()
                # the row that fired stays untouched; everything else bound to this record redraws
                self._sync_rows()
                self._notify()

            row = ctk.CTkCheckBox(
                self.list_frame,
                text=f"{c.path}  ({humanize.size(c.size)})",
                variable=var,
                command=on_toggle,
                text_color=theme.TEXT,
                font=theme.body_font(11),
            )
            row.pack(fill="x", anchor="w", pady=1)
            self._rows.append((c, var, row))

        # the button label has to describe what the NEXT press does, so it follows the scan
        self._sync_rows()

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
