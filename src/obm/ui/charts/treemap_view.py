# ---
# purpose: the treemap widget -- breadcrumb, canvas, debounced resize, chunked draw with a
#          generation counter so a resize mid-render never paints a stale layout
# exports: TreemapPanel
# depends: treemap_model.py, treemap_layout.py, treemap_interact.py, canvas_base.py, ui/worker.py
# gotcha: model+layout run on the worker thread (Worker), NOT the Tk thread -- only drawing
#         touches the canvas directly, chunked at CHUNK_SIZE items per after_idle
# ---
from __future__ import annotations

import os
import tkinter as tk
import tkinter.font as tkfont

import customtkinter as ctk

from ... import humanize
from .. import theme
from ..worker import Worker
from .canvas_base import draw_tile
from .squarify import Rect
from .treemap_interact import TreemapInteraction
from .treemap_layout import Tile, layout
from .treemap_model import TreeNode, build_tree

CHUNK_SIZE = 250
RESIZE_DEBOUNCE_MS = 120


class TreemapPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ctk.CTkLabel(header, text="Treemap", font=theme.heading_font(), text_color=theme.TEXT).pack(side="left")
        self.breadcrumb_label = ctk.CTkLabel(header, text="", font=theme.body_font(11), text_color=theme.MUTED)
        self.breadcrumb_label.pack(side="left", padx=12)
        self.up_button = ctk.CTkButton(header, text="Up", width=48, command=self._go_up, state="disabled")
        self.up_button.pack(side="right")
        self.filtered_switch = ctk.CTkSwitch(
            header, text="Show filtered", command=self._toggle_filtered, font=theme.body_font(11)
        )
        self.filtered_switch.pack(side="right", padx=8)

        self.canvas = tk.Canvas(self, bg=theme.PANEL_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas.bind("<Configure>", self._on_configure)

        self._label_font = tkfont.Font(family=theme.FONT_FAMILY, size=10)
        self._size_font = tkfont.Font(family=theme.FONT_FAMILY, size=8)
        self._interact = TreemapInteraction(self.canvas, on_drill_down=self._drill_down, on_open_file=self._open_file)
        self._layout_worker = Worker()

        self._result = None
        self._show_filtered = False
        self._breadcrumb: list[TreeNode] = []
        self._resize_job: str | None = None
        self._generation = 0

    def update_result(self, result) -> None:
        self._result = result
        self._rebuild_tree()

    def _rebuild_tree(self) -> None:
        if self._result is None:
            return
        root = build_tree(self._result.candidates, include_dropped=self._show_filtered)
        self._breadcrumb = [root]
        self._update_breadcrumb_label()
        self._request_layout()

    def _toggle_filtered(self) -> None:
        self._show_filtered = bool(self.filtered_switch.get())
        self._rebuild_tree()

    def _drill_down(self, path: str) -> None:
        node = self._find(self._breadcrumb[-1], path)
        if node is None or not node.is_dir or not node.children:
            return
        self._breadcrumb.append(node)
        self._update_breadcrumb_label()
        self._request_layout()

    def _go_up(self) -> None:
        if len(self._breadcrumb) <= 1:
            return
        self._breadcrumb.pop()
        self._update_breadcrumb_label()
        self._request_layout()

    def _find(self, node: TreeNode, path: str) -> TreeNode | None:
        if node.path == path:
            return node
        for child in node.children:
            found = self._find(child, path)
            if found is not None:
                return found
        return None

    def _open_file(self, path: str) -> None:
        try:
            os.startfile(os.path.dirname(path))  # noqa: S606 -- user-triggered, opens Explorer
        except OSError:
            pass

    def _update_breadcrumb_label(self) -> None:
        names = [n.name or "(root)" for n in self._breadcrumb]
        self.breadcrumb_label.configure(text=" › ".join(names))
        self.up_button.configure(state="normal" if len(self._breadcrumb) > 1 else "disabled")

    def _on_configure(self, event: tk.Event) -> None:
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(RESIZE_DEBOUNCE_MS, self._request_layout)

    def _request_layout(self) -> None:
        self._resize_job = None
        if not self._breadcrumb:
            return
        node = self._breadcrumb[-1]
        w = max(self.canvas.winfo_width(), 10)
        h = max(self.canvas.winfo_height(), 10)
        self._layout_worker.submit(lambda: layout(node, Rect(0, 0, w, h)))
        self.after(30, self._poll_layout)

    def _poll_layout(self) -> None:
        item = self._layout_worker.poll()
        if item is None:
            self.after(30, self._poll_layout)
            return
        kind, payload = item
        if kind == "ok":
            self._render(payload)

    def _render(self, tiles: list[Tile]) -> None:
        self._generation += 1
        gen = self._generation
        self._interact.set_tiles(tiles)
        self.canvas.delete("tile")
        self._draw_chunk(tiles, 0, gen)

    def _draw_chunk(self, tiles: list[Tile], start: int, gen: int) -> None:
        if gen != self._generation:
            return
        end = min(start + CHUNK_SIZE, len(tiles))
        for tile in tiles[start:end]:
            draw_tile(self.canvas, tile, self._label_font, self._size_font, humanize.size)
        if end < len(tiles):
            self.canvas.after_idle(lambda: self._draw_chunk(tiles, end, gen))
