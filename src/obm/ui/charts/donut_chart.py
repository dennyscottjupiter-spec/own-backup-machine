# ---
# purpose: donut chart Canvas widget -- keep/drop/placeholder proportions
# exports: DonutChart
# ---
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from .. import theme

_SLICE_COLORS = [theme.ACCENT, theme.DANGER, theme.WARNING, theme.SUCCESS, theme.MUTED]


class DonutChart(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, size: int = 160) -> None:
        super().__init__(master, fg_color="transparent")
        self.size = size
        self.canvas = tk.Canvas(self, width=size, height=size, bg=theme.PANEL_BG, highlightthickness=0)
        self.canvas.pack()
        self._items: list[tuple[str, int]] = []

    def update_data(self, items: list[tuple[str, int]]) -> None:
        self._items = [(name, v) for name, v in items if v > 0]
        self._redraw()

    def _redraw(self) -> None:
        self.canvas.delete("all")
        total = sum(v for _, v in self._items)
        if total <= 0:
            return

        pad = 10
        start = 90.0
        for i, (_, value) in enumerate(self._items):
            extent = 360.0 * value / total
            self.canvas.create_arc(
                pad, pad, self.size - pad, self.size - pad,
                start=start, extent=extent, fill=_SLICE_COLORS[i % len(_SLICE_COLORS)],
                outline=theme.PANEL_BG, width=2, style="pieslice",
            )
            start += extent

        inner = self.size * 0.55
        offset = (self.size - inner) / 2
        self.canvas.create_oval(offset, offset, offset + inner, offset + inner, fill=theme.PANEL_BG, outline="")
