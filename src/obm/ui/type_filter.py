# ---
# purpose: "back up only these kinds" -- one checkbox per file category, toggling
#          CandidateFile.selected, plus an all-categories-at-once toggle
# exports: TypeFilter
# depends: filter/classify.py, humanize.py, ui/{theme,category_peek}
# note: refresh_selection() re-reads the records into the boxes; update_result() rebuilds the rows
# gotcha: acts on every kept candidate of a category, not on the rows any other panel shows, so
#         panels bound to the same records must be refreshed from the on_change callback.
#         The peek button is the word "list", not a glyph: at two columns there is room for it,
#         and an emoji magnifier renders as tofu on a stock Windows Tk.
# ---
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import humanize
from ..filter.classify import category_of
from ..models import CandidateFile, DryRunResult
from . import theme
from .category_peek import open_category_window

COLUMNS = 2
PEEK_LABEL = "list"


class TypeFilter(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, on_change: Callable[[], None] | None = None) -> None:
        super().__init__(master, fg_color="transparent")
        self._on_change = on_change
        self._by_category: dict[str, list[CandidateFile]] = {}
        self._vars: dict[str, ctk.BooleanVar] = {}
        for column in range(COLUMNS):
            self.grid_columnconfigure(column, weight=1)

    def refresh_selection(self) -> None:
        """Someone else wrote CandidateFile.selected (the big-file rows do) -- re-read it into the
        checkboxes without rebuilding them, which would destroy a widget mid-click."""
        for category, var in self._vars.items():
            var.set(any(c.selected for c in self._by_category.get(category, ())))

    def all_selected(self) -> bool:
        return bool(self._by_category) and all(
            c.selected for files in self._by_category.values() for c in files
        )

    def set_all(self, selected: bool) -> None:
        """Every kept candidate at once -- the Summary panel's Select all / Select none."""
        for files in self._by_category.values():
            for c in files:
                c.selected = selected
        for var in self._vars.values():
            var.set(selected)
        if self._on_change is not None:
            self._on_change()

    def update_result(self, result: DryRunResult) -> None:
        for child in self.winfo_children():
            child.destroy()

        self._by_category = {}
        self._vars = {}
        for c in result.candidates:
            if c.verdict == "keep" and "placeholder" not in c.tags:
                self._by_category.setdefault(category_of(c.path), []).append(c)

        if not self._by_category:
            ctk.CTkLabel(self, text="Nothing to back up", text_color=theme.MUTED, font=theme.body_font(11)).grid(
                row=0, column=0, sticky="w"
            )
            return

        ordered = sorted(self._by_category.items(), key=lambda kv: sum(c.size for c in kv[1]), reverse=True)
        for index, (category, files) in enumerate(ordered):
            var = ctk.BooleanVar(value=any(c.selected for c in files))
            self._vars[category] = var
            total = sum(c.size for c in files)

            def on_toggle(cat: str = category, v: ctk.BooleanVar = var) -> None:
                self._set_category(cat, v.get())

            def on_peek(cat: str = category) -> None:
                open_category_window(self.winfo_toplevel(), cat, self._by_category.get(cat, []))

            cell = ctk.CTkFrame(self, fg_color="transparent")
            cell.grid(row=index // COLUMNS, column=index % COLUMNS, sticky="w", padx=4, pady=2)
            ctk.CTkCheckBox(
                cell,
                text=f"{category} ({humanize.count(len(files))}, {humanize.size(total)})",
                variable=var,
                command=on_toggle,
                text_color=theme.TEXT,
                font=theme.body_font(11),
                checkbox_width=16,
                checkbox_height=16,
            ).pack(side="left")
            ctk.CTkButton(
                cell, text=PEEK_LABEL, width=38, height=20, fg_color=theme.BG,
                hover_color=theme.ACCENT, text_color=theme.MUTED,
                font=theme.body_font(10), command=on_peek,
            ).pack(side="left", padx=(6, 0))

    def _set_category(self, category: str, selected: bool) -> None:
        for c in self._by_category.get(category, ()):
            c.selected = selected
        if self._on_change is not None:
            self._on_change()
