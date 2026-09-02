# ---
# purpose: ONE Motion binding + reverse-order hit-test -- per-item Enter/Leave bindings are
#          exactly how tkinter stalls on thousands of items
# exports: TreemapInteraction
# depends: treemap_layout.Tile, humanize.py
# gotcha: acts only when the hit index CHANGES, and reuses one highlight rect + one tooltip
#          group -- never creates/deletes canvas items on every mouse-move tick.
#          A single click reports the whole Tile, never just its path -- the view needs
#          is_dir/is_more to tell "drill in" from "show this file" apart.
# ---
from __future__ import annotations

import tkinter as tk
from typing import Callable

from ... import humanize
from .treemap_layout import Tile


class TreemapInteraction:
    def __init__(
        self,
        canvas: tk.Canvas,
        on_tile_click: Callable[[Tile], None] | None = None,
        on_open_file: Callable[[str], None] | None = None,
    ) -> None:
        self.canvas = canvas
        self._tiles: list[Tile] = []
        self._hover_index: int | None = None
        self._highlight_id: int | None = None
        self._tooltip_bg_id: int | None = None
        self._tooltip_text_id: int | None = None
        self._on_tile_click = on_tile_click
        self._on_open_file = on_open_file

        canvas.bind("<Motion>", self._on_motion)
        canvas.bind("<Leave>", self._on_leave)
        canvas.bind("<Button-1>", self._on_click)
        canvas.bind("<Double-Button-1>", self._on_double_click)

    def set_tiles(self, tiles: list[Tile]) -> None:
        self._tiles = tiles
        self._hover_index = None
        self._clear_highlight()

    def _hit_test(self, x: float, y: float) -> int | None:
        for i in range(len(self._tiles) - 1, -1, -1):
            r = self._tiles[i].rect
            if r.x <= x <= r.x + r.w and r.y <= y <= r.y + r.h:
                return i
        return None

    def _clear_highlight(self) -> None:
        for attr in ("_highlight_id", "_tooltip_bg_id", "_tooltip_text_id"):
            item_id = getattr(self, attr)
            if item_id is not None:
                self.canvas.delete(item_id)
                setattr(self, attr, None)

    def _on_motion(self, event: tk.Event) -> None:
        idx = self._hit_test(event.x, event.y)
        if idx == self._hover_index:
            return
        self._hover_index = idx
        self._clear_highlight()
        if idx is None:
            return

        tile = self._tiles[idx]
        r = tile.rect
        self._highlight_id = self.canvas.create_rectangle(
            r.x, r.y, r.x + r.w, r.y + r.h, outline="#ffffff", width=2, tags=("hover",)
        )
        text = f"{tile.label} ({humanize.count(tile.more_count)} items)" if tile.is_more else tile.label
        self._tooltip_bg_id = self.canvas.create_rectangle(
            event.x + 12, event.y + 14, event.x + 14 + 7 * len(text), event.y + 32,
            fill="#000000", outline="", tags=("hover",),
        )
        self._tooltip_text_id = self.canvas.create_text(
            event.x + 16, event.y + 23, text=text, anchor="w", fill="#ffffff", tags=("hover",)
        )

    def _on_leave(self, event: tk.Event) -> None:
        self._hover_index = None
        self._clear_highlight()

    def _on_click(self, event: tk.Event) -> None:
        idx = self._hit_test(event.x, event.y)
        if idx is None:
            return
        if self._on_tile_click:
            self._on_tile_click(self._tiles[idx])

    def _on_double_click(self, event: tk.Event) -> None:
        idx = self._hit_test(event.x, event.y)
        if idx is None:
            return
        tile = self._tiles[idx]
        if not tile.is_dir and not tile.is_more and self._on_open_file:
            self._on_open_file(tile.path)
