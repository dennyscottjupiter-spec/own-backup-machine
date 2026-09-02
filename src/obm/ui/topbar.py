# ---
# purpose: title bar with a status label and the rescan button
# exports: TopBar
# ---
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from . import theme


class TopBar(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk, on_scan: Callable[[], None]) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)

        title = ctk.CTkLabel(self, text="own-backup-machine", font=theme.heading_font(18), text_color=theme.TEXT)
        title.pack(side="left", padx=16, pady=10)

        self.status_label = ctk.CTkLabel(self, text="Ready", font=theme.body_font(), text_color=theme.MUTED)
        self.status_label.pack(side="left", padx=8)

        rescan_btn = ctk.CTkButton(self, text="Rescan", command=on_scan, fg_color=theme.ACCENT)
        rescan_btn.pack(side="right", padx=16, pady=10)

    def set_status(self, text: str) -> None:
        self.status_label.configure(text=text)
