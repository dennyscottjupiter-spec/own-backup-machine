# ---
# purpose: scan-issue list collapsed one row per root folder, plus a Copy button that puts every
#          issue (not just the shown ones) on the clipboard -- issues are a first-class output,
#          never swallowed
# exports: IssuesPanel
# depends: scan/issues.py, ui/panel_header.py
# gotcha: the Copy button is packed after the header's Expand button so it lands to its left.
#         Group children are built on first expand, never up front -- a noisy volume can produce
#         issues by the hundred-thousand and one widget each would freeze Tk.
#         Sizes come from ScanIssue.size, resolved in the scan worker -- never stat here.
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import humanize
from ..models import DryRunResult
from ..scan.issues import KIND_LABELS, IssueGroup, group_by_root, relative_to, report, size_prefix
from . import panel_header, theme

MAX_SHOWN = 100
MAX_PER_GROUP = 200
COPIED_RESET_MS = 1500
COLLAPSED = "▶"
EXPANDED = "▼"


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

        if not result.issues:
            ctk.CTkLabel(
                self.list_frame, text="No issues", text_color=theme.MUTED, font=theme.body_font(11)
            ).pack(anchor="w")
            return

        groups = group_by_root(result.issues)
        for group in groups[: self._max_shown]:
            if len(group.issues) == 1:
                self._add_issue_row(self.list_frame, group.issues[0], group.issues[0].path, indent=0)
            else:
                self._add_group(group)

        hidden = len(groups) - self._max_shown
        if hidden > 0:
            ctk.CTkLabel(
                self.list_frame,
                text=f"+{humanize.count(hidden)} more folders with issues not shown",
                text_color=theme.MUTED,
                font=theme.body_font(11),
            ).pack(anchor="w", pady=(4, 0))

    def _add_group(self, group: IssueGroup) -> None:
        """One collapsed row for the whole folder; its children are built on the first click, so a
        folder with 40k issues costs exactly one widget until someone actually asks to see it."""
        holder = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        holder.pack(fill="x", anchor="w")

        toggle = ctk.CTkButton(
            holder, text=self._group_label(group, COLLAPSED), anchor="w", height=22,
            fg_color="transparent", hover_color=theme.BG, text_color=theme.WARNING,
            font=theme.body_font(11),
        )
        toggle.pack(fill="x", anchor="w", pady=1)
        body = ctk.CTkFrame(holder, fg_color="transparent")
        built = False

        def on_click() -> None:
            nonlocal built
            if not built:
                self._fill_group(body, group)
                built = True
            if body.winfo_ismapped():
                body.pack_forget()
                toggle.configure(text=self._group_label(group, COLLAPSED))
            else:
                body.pack(fill="x", anchor="w")
                toggle.configure(text=self._group_label(group, EXPANDED))

        toggle.configure(command=on_click)

    def _fill_group(self, body: ctk.CTkFrame, group: IssueGroup) -> None:
        for issue in group.issues[:MAX_PER_GROUP]:
            self._add_issue_row(body, issue, relative_to(group.root, issue.path), indent=18)
        if len(group.issues) > MAX_PER_GROUP:
            ctk.CTkLabel(
                body,
                text=f"+{humanize.count(len(group.issues) - MAX_PER_GROUP)} more in this folder",
                text_color=theme.MUTED,
                font=theme.body_font(11),
                anchor="w",
            ).pack(fill="x", anchor="w", padx=(18, 0))

    @staticmethod
    def _group_label(group: IssueGroup, glyph: str) -> str:
        total = humanize.size(group.total_size) if group.total_size else "?"
        return f"{glyph} [{total}] {humanize.count(len(group.issues))} issues — {group.root}"

    @staticmethod
    def _add_issue_row(master: ctk.CTkBaseClass, issue, text: str, indent: int) -> None:
        label = KIND_LABELS.get(issue.kind, issue.kind)
        ctk.CTkLabel(
            master,
            text=f"[{size_prefix(issue)}] [{label}] {text}",
            text_color=theme.WARNING,
            font=theme.body_font(11),
            anchor="w",
        ).pack(fill="x", anchor="w", padx=(indent, 0), pady=1)

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
