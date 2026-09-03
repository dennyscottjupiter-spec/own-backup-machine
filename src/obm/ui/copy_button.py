# ---
# purpose: the shared "⧉ Copy" button -- puts whatever its provider returns on the clipboard and
#          says so for a moment
# exports: LABEL, CopyButton
# depends: ui/theme.py
# gotcha: Windows only hands the clipboard over once the app has processed events, so update()
#         after append() is required, not cosmetic
# ---
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from . import theme

LABEL = "⧉ Copy"
COPIED_RESET_MS = 1500


class CopyButton(ctk.CTkButton):
    def __init__(self, master: ctk.CTkBaseClass, text_provider: Callable[[], str], **kwargs) -> None:
        kwargs.setdefault("width", 72)
        kwargs.setdefault("height", 24)
        kwargs.setdefault("fg_color", theme.BG)
        kwargs.setdefault("font", theme.body_font(11))
        super().__init__(master, text=LABEL, command=self._copy, **kwargs)
        self._text_provider = text_provider

    def _copy(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self._text_provider())
        self.update()
        self.configure(text="Copied")
        self.after(COPIED_RESET_MS, self._reset)

    def _reset(self) -> None:
        if self.winfo_exists():
            self.configure(text=LABEL)
