# ---
# purpose: virtualized top-N scan-issue list -- issues are a first-class output, never swallowed
# exports: IssuesPanel
# depends: scan/issues.py, ui/panel_header.py
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import humanize
from ..models import DryRunResult
from ..scan.issues import KIND_LABELS
from . import panel_header, theme

MAX_SHOWN = 100


class IssuesPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, on_expand=None, max_shown: int = MAX_SHOWN) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)
        self._max_shown = max_shown

        panel_header.build(self, "Issues", on_expand)

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def update_result(self, result: DryRunResult) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        issues = result.issues
        for issue in issues[: self._max_shown]:
            label = KIND_LABELS.get(issue.kind, issue.kind)
            row = ctk.CTkLabel(
                self.list_frame,
                text=f"[{label}] {issue.path}",
                text_color=theme.WARNING,
                font=theme.body_font(11),
                anchor="w",
            )
            row.pack(fill="x", anchor="w", pady=1)

        hidden = len(issues) - self._max_shown
        if hidden > 0:
            more = ctk.CTkLabel(
                self.list_frame,
                text=f"+{humanize.count(hidden)} more issues not shown",
                text_color=theme.MUTED,
                font=theme.body_font(11),
            )
            more.pack(anchor="w", pady=(4, 0))
        elif not issues:
            row = ctk.CTkLabel(self.list_frame, text="No issues", text_color=theme.MUTED, font=theme.body_font(11))
            row.pack(anchor="w")
