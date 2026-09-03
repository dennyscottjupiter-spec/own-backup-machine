# ---
# purpose: shared CTkToplevel setup -- size, centering over the main window, raise-to-front and
#          the Escape-closes-this-window binding every popup in the app gets
# exports: place_over(), open_panel_window(), open_text_window()
# depends: ui/theme.py
# gotcha: CustomTkinter builds a CTkToplevel with a deferred internal update, so lift()/focus at
#         construction time is undone ~200ms later and the window lands behind the main one --
#         the raise MUST be re-issued from an after() callback. Every popup goes through
#         place_over(), which is what makes one Escape binding here cover all of them.
# ---
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from . import theme

RAISE_DELAY_MS = 250


def place_over(win: ctk.CTkToplevel, master, width: int, height: int) -> None:
    master.update_idletasks()
    mx, my = master.winfo_rootx(), master.winfo_rooty()
    mw, mh = master.winfo_width(), master.winfo_height()
    x = max(mx + (mw - width) // 2, 0)
    y = max(my + (mh - height) // 2, 0)
    win.geometry(f"{width}x{height}+{x}+{y}")
    win.bind("<Escape>", lambda _event: win.destroy())
    _raise(win)
    win.after(RAISE_DELAY_MS, lambda: _raise(win))


def _raise(win: ctk.CTkToplevel) -> None:
    if not win.winfo_exists():
        return
    win.deiconify()
    win.lift()
    win.focus_force()


def open_panel_window(master, title: str, factory: Callable[[ctk.CTkBaseClass], ctk.CTkFrame], result) -> None:
    """Show one panel class full-size in its own window, fed the current scan result."""
    win = ctk.CTkToplevel(master)
    win.title(title)
    win.configure(fg_color=theme.BG)
    panel = factory(win)
    panel.pack(fill="both", expand=True, padx=12, pady=12)
    if result is not None:
        panel.update_result(result)
    place_over(win, master, 1100, 720)


def open_text_window(master, title: str, text: str) -> None:
    win = ctk.CTkToplevel(master)
    win.title(title)
    win.configure(fg_color=theme.BG)
    box = ctk.CTkTextbox(win, fg_color=theme.PANEL_BG, text_color=theme.TEXT, font=theme.body_font(12))
    box.pack(fill="both", expand=True, padx=12, pady=12)
    box.insert("1.0", text)
    box.configure(state="disabled")
    place_over(win, master, 620, 260)
