# ---
# purpose: donut chart Canvas widget -- selected/deselected/dropped proportions
# exports: DonutChart
# gotcha: zero-valued slices are dropped, so a caller that cares which colour means what must pass
#         `colors` -- the default palette is positional and shifts when a slice empties out
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
        self._slices: list[tuple[str, int, str]] = []

    def update_data(self, items: list[tuple[str, int]], colors: list[str] | None = None) -> None:
        palette = colors or _SLICE_COLORS
        # colours are paired up BEFORE the empty slices are dropped, so an emptied segment does not
        # shift every colour after it onto the wrong meaning
        paired = [(name, v, palette[i % len(palette)]) for i, (name, v) in enumerate(items)]
        self._slices = [s for s in paired if s[1] > 0]
        self._redraw()

    def _redraw(self) -> None:
        self.canvas.delete("all")
        total = sum(v for _, v, _ in self._slices)
        if total <= 0:
            return

        pad = 10
        start = 90.0
        for _, value, color in self._slices:
            extent = 360.0 * value / total
            self.canvas.create_arc(
                pad, pad, self.size - pad, self.size - pad,
                start=start, extent=extent, fill=color,
                outline=theme.PANEL_BG, width=2, style="pieslice",
            )
            start += extent

        inner = self.size * 0.55
        offset = (self.size - inner) / 2
        self.canvas.create_oval(offset, offset, offset + inner, offset + inner, fill=theme.PANEL_BG, outline="")
