# ---
# purpose: shared Canvas drawing helpers -- category palette, cached text truncation, tile drawing
# exports: CATEGORY_COLORS, color_for_category(), truncate(), draw_tile()
# gotcha: truncate() calls font.measure() at most twice (full string, one candidate) -- measuring
#         every tile on every frame is exactly the freeze source Hard Part 7 warns about
# ---
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from .. import theme

CATEGORY_COLORS = {
    "document": "#3b82f6",
    "photo": "#22c55e",
    "video": "#ef4444",
    "audio": "#f59e0b",
    "code": "#8b5cf6",
    "archive": "#06b6d4",
    "program": "#ec4899",
    "llm model": "#14b8a6",
    "unknown": "#6b7280",
    "filtered": "#7f1d1d",
}

_avg_char_width_cache: dict[str, float] = {}


def color_for_category(category: str) -> str:
    return CATEGORY_COLORS.get(category, CATEGORY_COLORS["unknown"])


def _avg_char_width(font: tkfont.Font) -> float:
    key = f"{font.cget('family')}-{font.cget('size')}"
    cached = _avg_char_width_cache.get(key)
    if cached is None:
        sample = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        cached = font.measure(sample) / len(sample)
        _avg_char_width_cache[key] = cached
    return cached


def truncate(text: str, max_width: float, font: tkfont.Font) -> str:
    if max_width <= 0:
        return ""
    if font.measure(text) <= max_width:
        return text
    width_per_char = _avg_char_width(font) or 1.0
    approx_chars = max(1, int(max_width / width_per_char) - 1)
    candidate = text[:approx_chars] + "…"
    while len(candidate) > 1 and font.measure(candidate) > max_width:
        candidate = candidate[:-2] + "…"
    return candidate


def draw_tile(canvas: tk.Canvas, tile, label_font: tkfont.Font, size_font: tkfont.Font, humanize_size) -> None:
    r = tile.rect
    x0, y0, x1, y1 = r.x, r.y, r.x + r.w, r.y + r.h
    color = theme.MUTED if tile.is_more else color_for_category(tile.category or "unknown")
    canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=theme.PANEL_BG, width=1, tags=("tile",))

    if tile.is_dir and 0 < tile.depth <= 2:
        canvas.create_rectangle(x0, y0, x1, y0 + 18, fill="", outline=theme.PANEL_BG, tags=("tile",))

    if r.w >= 60 and r.h >= 16:
        label = truncate(tile.label, r.w - 8, label_font)
        canvas.create_text(x0 + 4, y0 + 2, text=label, anchor="nw", fill="#ffffff", font=label_font, tags=("tile",))

    if r.h >= 32 and not tile.is_more:
        canvas.create_text(
            x0 + 4, y0 + 18, text=humanize_size(tile.size), anchor="nw",
            fill="#d1d5db", font=size_font, tags=("tile",),
        )
