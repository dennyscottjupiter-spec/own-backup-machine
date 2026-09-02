# ---
# purpose: virtualized top-N scan-issue list, plus a Copy button that puts every issue (not just
#          the shown ones) on the clipboard -- issues are a first-class output, never swallowed
# exports: IssuesPanel
# depends: scan/issues.py, ui/panel_header.py
# gotcha: the Copy button is packed after the header's Expand button so it lands to its left
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import humanize
from ..models import DryRunResult
from ..scan.issues import KIND_LABELS, report
from . import panel_header, theme

MAX_SHOWN = 100
COPIED_RESET_MS = 1500


class IssuesPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, on_expand=None, max_shown: int = MAX_SHOWN) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)
        self._max_shown = max_shown
        self._result: DryRunResult | None = None

        header = panel_header.build(self, "Issues", on_expand)
        self.copy_button = ctk.CTkButton(
            header, text="⧉ Copy", width=72, height=24, fg_color=theme.BG,
            font=theme.body_font(11), command=self._copy,
        )
        self.copy_button.pack(side="right", padx=(0, 6))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def update_result(self, result: DryRunResult) -> None:
        self._result = result
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

    def _copy(self) -> None:
        issues = self._result.issues if self._result is not None else []
        self.clipboard_clear()
        self.clipboard_append(report(issues))
        self.update()  # Windows only hands the clipboard over once the app has processed events
        self.copy_button.configure(text="Copied")
        self.after(COPIED_RESET_MS, self._reset_copy_label)

    def _reset_copy_label(self) -> None:
        if self.copy_button.winfo_exists():
            self.copy_button.configure(text="⧉ Copy")
