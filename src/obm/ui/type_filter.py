# ---
# purpose: "back up only these kinds" -- one checkbox per file category, toggling CandidateFile.selected
# exports: TypeFilter
# depends: filter/classify.py, humanize.py, ui/theme.py
# gotcha: acts on every kept candidate of a category, not on the rows any other panel shows, so
#         panels bound to the same records must be refreshed from the on_change callback
# ---
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import humanize
from ..filter.classify import category_of
from ..models import CandidateFile, DryRunResult
from . import theme

COLUMNS = 3


class TypeFilter(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, on_change: Callable[[], None] | None = None) -> None:
        super().__init__(master, fg_color="transparent")
        self._on_change = on_change
        self._by_category: dict[str, list[CandidateFile]] = {}
        for column in range(COLUMNS):
            self.grid_columnconfigure(column, weight=1)

    def update_result(self, result: DryRunResult) -> None:
        for child in self.winfo_children():
            child.destroy()

        self._by_category = {}
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
            total = sum(c.size for c in files)

            def on_toggle(cat: str = category, v: ctk.BooleanVar = var) -> None:
                self._set_category(cat, v.get())

            ctk.CTkCheckBox(
                self,
                text=f"{category} ({humanize.count(len(files))}, {humanize.size(total)})",
                variable=var,
                command=on_toggle,
                text_color=theme.TEXT,
                font=theme.body_font(11),
                checkbox_width=16,
                checkbox_height=16,
            ).grid(row=index // COLUMNS, column=index % COLUMNS, sticky="w", padx=4, pady=2)

    def _set_category(self, category: str, selected: bool) -> None:
        for c in self._by_category.get(category, ()):
            c.selected = selected
        if self._on_change is not None:
            self._on_change()
