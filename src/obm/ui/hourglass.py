# ---
# purpose: the animated hourglass shown while a run is archiving
# exports: Hourglass
# depends: ui/theme.py
# gotcha: drawn on a canvas rather than with the ⏳ character -- Tk 8.6 has no colour-emoji
#         renderer and would paint a tofu box on most Windows installs. Never store size in
#         self._w: tkinter keeps the widget's own Tcl pathname there
# ---
from __future__ import annotations

import customtkinter as ctk

from . import theme

FRAMES = 26
INTERVAL_MS = 90
MARGIN = 5


class Hourglass(ctk.CTkCanvas):
    def __init__(self, master: ctk.CTkBaseClass, width: int = 46, height: int = 64) -> None:
        super().__init__(master, width=width, height=height, bg=theme.PANEL_BG, highlightthickness=0)
        # NOT self._w / self._h: tkinter stores the widget's own Tcl pathname in self._w
        self._width = width
        self._height = height
        self._frame = 0
        self._running = False
        self._draw(0.0)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._tick()

    def stop(self) -> None:
        self._running = False
        self._draw(1.0)

    def _tick(self) -> None:
        if not self._running or not self.winfo_exists():
            return
        self._frame = (self._frame + 1) % FRAMES
        self._draw(self._frame / FRAMES)
        self.after(INTERVAL_MS, self._tick)

    def _draw(self, fallen: float) -> None:
        """`fallen` is the fraction of sand already in the lower bulb, 0..1."""
        self.delete("all")
        cx = self._width / 2
        hw = (self._width - 2 * MARGIN) / 2
        top, mid, bottom = MARGIN, self._height / 2, self._height - MARGIN

        self.create_polygon(cx - hw, top, cx + hw, top, cx, mid, outline=theme.MUTED, fill="", width=2)
        self.create_polygon(cx - hw, bottom, cx + hw, bottom, cx, mid, outline=theme.MUTED, fill="", width=2)

        left = 1.0 - fallen
        if left > 0.01:
            level = mid - (mid - top) * left
            self.create_polygon(
                cx - hw * left, level, cx + hw * left, level, cx, mid, fill=theme.ACCENT, outline=""
            )
        if fallen > 0.01:
            # the lower bulb is widest at its base, so the pile narrows as it rises
            pile = bottom - (bottom - mid) * fallen
            rest = 1.0 - fallen
            self.create_polygon(
                cx - hw, bottom, cx + hw, bottom, cx + hw * rest, pile, cx - hw * rest, pile,
                fill=theme.ACCENT, outline="",
            )
