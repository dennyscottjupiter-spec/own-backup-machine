# ---
# purpose: the draggable splitters between dashboard panels, and reading/writing their sash
#          positions so a resized dashboard comes back the same way next launch
# exports: SASH_WIDTH, make_paned(), read_sashes(), apply_sashes()
# depends: ui/theme.py
# gotcha: a sash coordinate only exists once Tk has laid the panes out, so apply_sashes() must run
#         from an after() callback, never during __init__ -- before that every sash reads as 0
# ---
from __future__ import annotations

import tkinter as tk

from . import theme

SASH_WIDTH = 8


def make_paned(master, orient: str) -> tk.PanedWindow:
    return tk.PanedWindow(
        master,
        orient=orient,
        bg=theme.BG,
        sashwidth=SASH_WIDTH,
        sashrelief="flat",
        sashpad=0,
        borderwidth=0,
        showhandle=False,
        opaqueresize=False,  # drag a guideline, not a live relayout -- the treemap is expensive
    )


def _axis(paned: tk.PanedWindow) -> int:
    return 0 if str(paned.cget("orient")) == "horizontal" else 1


def read_sashes(paned: tk.PanedWindow) -> list[int]:
    """The position of each sash along the split axis, left/top first."""
    axis = _axis(paned)
    return [paned.sash_coord(i)[axis] for i in range(len(paned.panes()) - 1)]


def apply_sashes(paned: tk.PanedWindow, values: list[int]) -> None:
    """Restore saved positions, skipping any that no longer fit the current window."""
    axis = _axis(paned)
    limit = paned.winfo_width() if axis == 0 else paned.winfo_height()
    for i, value in enumerate(values):
        if i >= len(paned.panes()) - 1 or value <= 0 or value >= limit:
            continue
        coord = list(paned.sash_coord(i))
        coord[axis] = value
        paned.sash_place(i, coord[0], coord[1])
