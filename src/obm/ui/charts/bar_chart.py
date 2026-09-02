# ---
# purpose: horizontal bar chart Canvas widget -- category-by-size breakdown
# exports: BarChart
# depends: humanize.py
# ---
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ... import humanize
from .. import theme
from .canvas_base import color_for_category


class BarChart(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color="transparent")
        self.canvas = tk.Canvas(self, bg=theme.PANEL_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._redraw())
        self._items: list[tuple[str, int]] = []

    def update_data(self, items: list[tuple[str, int]]) -> None:
        self._items = sorted(items, key=lambda kv: -kv[1])
        self._redraw()

    def _redraw(self) -> None:
        self.canvas.delete("all")
        if not self._items:
            return
        width = self.canvas.winfo_width() or 400
        row_h = 22
        max_val = max(v for _, v in self._items) or 1
        label_w = 90

        for i, (name, value) in enumerate(self._items):
            y = i * row_h + 4
            bar_w = max(2.0, (width - label_w - 60) * value / max_val)
            self.canvas.create_text(4, y + 8, text=name, anchor="w", fill=theme.TEXT, font=(theme.FONT_FAMILY, 10))
            self.canvas.create_rectangle(
                label_w, y, label_w + bar_w, y + 14, fill=color_for_category(name), outline=""
            )
            self.canvas.create_text(
                label_w + bar_w + 6, y + 8, text=humanize.size(value), anchor="w",
                fill=theme.MUTED, font=(theme.FONT_FAMILY, 9),
            )
