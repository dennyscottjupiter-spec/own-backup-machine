# ---
# purpose: the "save the archive here" selector -- every writable drive, Desktop and Downloads,
#          plus a folder browser
# exports: DestPicker
# depends: destinations.py, ui/theme.py
# gotcha: an empty config resolves to destinations.PREFERRED_DRIVE, so the caller must read
#         get() back after construction and persist it
# ---
from __future__ import annotations

import os
import tkinter.filedialog as filedialog
from typing import Callable

import customtkinter as ctk

from .. import destinations
from . import theme

BROWSE = "Browse..."


class DestPicker(ctk.CTkFrame):
    def __init__(
        self, master: ctk.CTkBaseClass, current: str, on_change: Callable[[str], None] | None = None
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._on_change = on_change

        options = destinations.destination_options()
        self._current = destinations.resolve_default(current, options)
        if self._current and self._current not in options:
            options.insert(0, self._current)

        self._var = ctk.StringVar(value=self._current)
        ctk.CTkLabel(self, text="Save to", font=theme.body_font(11), text_color=theme.MUTED).pack(
            side="left", padx=(0, 6)
        )
        self._menu = ctk.CTkOptionMenu(
            self, values=options + [BROWSE], variable=self._var, command=self._on_select,
            width=190, font=theme.body_font(11), fg_color=theme.BG, button_color=theme.BG,
        )
        self._menu.pack(side="left")

    def get(self) -> str:
        return self._current

    def _on_select(self, choice: str) -> None:
        if choice == BROWSE:
            picked = filedialog.askdirectory(initialdir=self._current or None)
            if not picked:
                self._var.set(self._current)
                return
            choice = os.path.normpath(picked)
            values = list(self._menu.cget("values"))
            if choice not in values:
                self._menu.configure(values=[choice] + values)

        self._current = choice
        self._var.set(choice)
        if self._on_change is not None:
            self._on_change(choice)
