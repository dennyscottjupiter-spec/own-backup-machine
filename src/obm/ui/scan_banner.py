# ---
# purpose: the strip under the title bar that shows a scan running -- how far along, how many
#          files so far, and which folder it is in right now
# exports: ScanBanner
# depends: humanize.py, ui/theme.py
# gotcha: show() must pack with before=<the expanding body> -- a fill="x" strip packed after an
#         expand=True sibling finds an exhausted cavity and Tk leaves it silently unmapped.
#         With no previous scan to compare against there is no honest percentage, so the bar runs
#         indeterminate rather than inventing one
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import humanize
from . import theme

CONTENT_W = 560
PATH_SEGMENTS = 3  # enough to recognise where you are without the strip jumping about
PATH_CHARS = 54


def _short_path(path: str) -> str:
    parts = path.replace("/", "\\").split("\\")[:-1]
    if len(parts) <= PATH_SEGMENTS:
        return "\\".join(parts)
    return "...\\" + "\\".join(parts[-PATH_SEGMENTS:])


class ScanBanner(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)
        self._running = False

        # fixed size, propagation off: the caption changes on every tick, and a frame that sizes
        # itself to its content would make the whole centred block twitch left and right
        inner = ctk.CTkFrame(self, fg_color="transparent", width=CONTENT_W, height=62)
        inner.pack_propagate(False)
        inner.pack(padx=16, pady=8)

        heading = ctk.CTkFrame(inner, fg_color="transparent")
        heading.pack(fill="x")
        ctk.CTkLabel(
            heading, text="Looking at every file on your drive", font=theme.body_font(13), text_color=theme.TEXT
        ).pack(side="left")
        self.percent_label = ctk.CTkLabel(heading, text="", font=theme.heading_font(13), text_color=theme.ACCENT)
        self.percent_label.pack(side="right", padx=(24, 0))

        self.bar = ctk.CTkProgressBar(
            inner, width=CONTENT_W, height=5, corner_radius=3, fg_color=theme.BG, progress_color=theme.ACCENT
        )
        self.bar.pack(fill="x", pady=(8, 6))

        self.detail_label = ctk.CTkLabel(inner, text="", font=theme.body_font(11), text_color=theme.MUTED)
        self.detail_label.pack(anchor="w")

    def show(self, before: ctk.CTkBaseClass) -> None:
        self._running = True
        self.bar.configure(mode="indeterminate")
        self.bar.start()
        self.percent_label.configure(text="")
        self.detail_label.configure(text="Starting")
        self.pack(fill="x", padx=12, pady=(0, 6), before=before)

    def hide(self) -> None:
        self._running = False
        self.bar.stop()
        self.pack_forget()

    def update_scan(self, seen: int, expected: int, path: str) -> None:
        if not self._running:
            return

        if expected > 0:
            if self.bar.cget("mode") != "determinate":
                self.bar.stop()
                self.bar.configure(mode="determinate")
            share = min(seen / expected, 0.99)
            self.bar.set(share)
            self.percent_label.configure(text=f"{share * 100:.0f}%")

        line = f"{humanize.count(seen)} files so far"
        where = _short_path(path)
        if where:
            line += f"  ·  {where}"
        self.detail_label.configure(text=line[:PATH_CHARS + 24])
