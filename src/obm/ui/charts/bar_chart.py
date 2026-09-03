# ---
# purpose: horizontal bar chart Canvas widget -- category-by-size breakdown, with the still-selected
#          share drawn bright inside the dimmed scan total
# exports: BarChart
# depends: humanize.py, palette.py
# gotcha: a deselected category keeps its row and its full-length dim bar -- the user is choosing
#         what to give up and has to be able to see it. Rows never disappear on a checkbox press.
# ---
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ... import humanize, palette
from .. import theme
from .canvas_base import color_for_category

ROW_H = 22
LABEL_W = 90
BAR_H = 14
# the caption sits past the end of the longest bar, so the gutter has to fit it: "1.5 GB" needs
# far less room than "820.4 MB of 1.5 GB", and the long form only appears once something is deselected
GUTTER_W = 60
GUTTER_W_COMPARED = 150


class BarChart(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, height: int = 140) -> None:
        super().__init__(master, fg_color="transparent", height=height)
        self.pack_propagate(False)
        self.canvas = tk.Canvas(self, bg=theme.PANEL_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._redraw())
        self._items: list[tuple[str, int]] = []
        self._selected: dict[str, int] = {}
        self._full = True

    def update_data(self, items: list[tuple[str, int]], selected: dict[str, int] | None = None) -> None:
        """`items` is the scan total per category; `selected` the still-ticked bytes of each one.
        Omitting `selected` means "everything counts", which is what a fresh scan shows."""
        self._items = sorted(items, key=lambda kv: -kv[1])
        self._selected = dict(selected) if selected is not None else {}
        self._full = selected is None
        self._redraw()

    def _redraw(self) -> None:
        self.canvas.delete("all")
        if not self._items:
            return
        width = self.canvas.winfo_width() or 400
        max_val = max(v for _, v in self._items) or 1
        compared = not self._full and any(self._selected.get(n, 0) != v for n, v in self._items)
        track_w = max(20, width - LABEL_W - (GUTTER_W_COMPARED if compared else GUTTER_W))

        for i, (name, value) in enumerate(self._items):
            y = i * ROW_H + 4
            picked = value if self._full else self._selected.get(name, 0)
            color = color_for_category(name)
            bar_w = max(2.0, track_w * value / max_val)

            self.canvas.create_text(
                4, y + 8, text=name, anchor="w",
                fill=theme.TEXT if picked else theme.MUTED, font=(theme.FONT_FAMILY, 10),
            )
            self.canvas.create_rectangle(
                LABEL_W, y, LABEL_W + bar_w, y + BAR_H, fill=palette.dim(color), outline=""
            )
            if picked:
                picked_w = max(2.0, track_w * picked / max_val)
                self.canvas.create_rectangle(LABEL_W, y, LABEL_W + picked_w, y + BAR_H, fill=color, outline="")

            caption = (
                humanize.size(value)
                if picked == value
                else f"{humanize.size(picked)} of {humanize.size(value)}"
            )
            self.canvas.create_text(
                LABEL_W + bar_w + 6, y + 8, text=caption, anchor="w",
                fill=theme.MUTED, font=(theme.FONT_FAMILY, 9),
            )
