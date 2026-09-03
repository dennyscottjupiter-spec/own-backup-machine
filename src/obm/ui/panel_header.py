# ---
# purpose: the shared panel title row -- heading plus the optional "open this panel in its own
#          window" button, so the cramped dashboard tiles all get the same escape hatch
# exports: EXPAND_GLYPH, build()
# depends: ui/theme.py
# gotcha: the expand button is a bare glyph to keep the dashboard uncluttered -- U+26F6 (a screen
#         outline) is in Segoe UI Symbol, so it renders on a stock Windows without a font fallback
# ---
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from . import theme

EXPAND_GLYPH = "⛶"


def build(panel: ctk.CTkBaseClass, title: str, on_expand: Callable[[], None] | None = None) -> ctk.CTkFrame:
    header = ctk.CTkFrame(panel, fg_color="transparent")
    header.pack(fill="x", padx=12, pady=(10, 2))
    ctk.CTkLabel(header, text=title, font=theme.heading_font(), text_color=theme.TEXT).pack(side="left")
    if on_expand is not None:
        ctk.CTkButton(
            header, text=EXPAND_GLYPH, width=28, height=24, fg_color=theme.BG,
            font=theme.body_font(15), command=on_expand,
        ).pack(side="right")
    return header
