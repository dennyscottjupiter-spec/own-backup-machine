# ---
# purpose: the "what is actually in this category" popup -- the biggest files of one category,
#          grouped by folder, so ticking a box in the type filter is never a blind guess
# exports: open_category_window()
# depends: ui/{dialog,theme}, palette.py, humanize.py, models.CandidateFile
# gotcha: capped at MAX_ROWS widgets like every other list in the app -- a category can hold
#         hundreds of thousands of files and one CTkLabel each freezes Tk
# ---
from __future__ import annotations

import os

import customtkinter as ctk

from .. import humanize, palette
from ..models import CandidateFile
from . import dialog, theme

MAX_ROWS = 300
PATH_LIMIT = 78


def open_category_window(master, category: str, files: list[CandidateFile]) -> None:
    win = ctk.CTkToplevel(master)
    win.title(f"{category} files")
    win.configure(fg_color=theme.BG)
    _build(win, category, files)
    dialog.place_over(win, master, 820, 620)


def _build(win: ctk.CTkToplevel, category: str, files: list[CandidateFile]) -> None:
    color = palette.color_for_category(category)

    head = ctk.CTkFrame(win, fg_color="transparent")
    head.pack(fill="x", padx=16, pady=(14, 4))
    ctk.CTkLabel(head, text="●", font=theme.heading_font(16), text_color=color).pack(side="left", padx=(0, 8))
    ctk.CTkLabel(head, text=category, font=theme.heading_font(18), text_color=theme.TEXT).pack(side="left")
    ctk.CTkLabel(
        head,
        text=f"{humanize.count(len(files))} files, {humanize.size(sum(f.size for f in files))}",
        font=theme.body_font(12),
        text_color=theme.MUTED,
    ).pack(side="left", padx=12)

    body = ctk.CTkScrollableFrame(win, fg_color=theme.PANEL_BG, corner_radius=8)
    body.pack(fill="both", expand=True, padx=16, pady=(4, 16))
    body.grid_columnconfigure(0, weight=1)

    shown = 0
    row = 0
    for folder, group in group_by_folder(files):
        if shown >= MAX_ROWS:
            break
        ctk.CTkLabel(
            body, text=_shorten(folder or "(root)"), font=theme.body_font(11), text_color=color, anchor="w"
        ).grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 2))
        row += 1
        for c in group:
            if shown >= MAX_ROWS:
                break
            ctk.CTkLabel(
                body, text=os.path.basename(c.path), font=theme.body_font(12), text_color=theme.TEXT, anchor="w"
            ).grid(row=row, column=0, sticky="ew", padx=(24, 8))
            ctk.CTkLabel(
                body, text=humanize.size(c.size), font=theme.body_font(11), text_color=theme.MUTED, anchor="e"
            ).grid(row=row, column=1, sticky="e", padx=(8, 12))
            row += 1
            shown += 1

    hidden = len(files) - shown
    if hidden > 0:
        ctk.CTkLabel(
            body,
            text=f"+{humanize.count(hidden)} more not shown",
            font=theme.body_font(11),
            text_color=theme.MUTED,
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 6))


def group_by_folder(files: list[CandidateFile]) -> list[tuple[str, list[CandidateFile]]]:
    """Folders ordered by how much of the category they hold, files inside them by size."""
    by_folder: dict[str, list[CandidateFile]] = {}
    for c in files:
        by_folder.setdefault(os.path.dirname(c.path), []).append(c)
    for group in by_folder.values():
        group.sort(key=lambda c: c.size, reverse=True)
    return sorted(by_folder.items(), key=lambda kv: sum(c.size for c in kv[1]), reverse=True)


def _shorten(path: str) -> str:
    return path if len(path) <= PATH_LIMIT else "..." + path[-(PATH_LIMIT - 3):]
