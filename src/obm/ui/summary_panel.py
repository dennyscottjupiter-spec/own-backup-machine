# ---
# purpose: keep/drop totals + a per-category breakdown, refreshed after every scan
# exports: SummaryPanel
# depends: pipeline/aggregate.py
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import humanize
from ..models import DryRunResult
from ..pipeline.aggregate import build_summary
from . import theme


class SummaryPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)

        heading = ctk.CTkLabel(self, text="Summary", font=theme.heading_font(), text_color=theme.TEXT)
        heading.pack(anchor="w", padx=16, pady=(12, 4))

        self.totals_label = ctk.CTkLabel(
            self, text="Scanning...", font=theme.body_font(), text_color=theme.TEXT, justify="left"
        )
        self.totals_label.pack(anchor="w", padx=16, pady=4)

        self.category_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.category_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def update_result(self, result: DryRunResult) -> None:
        summary = build_summary(result.candidates, result.issues)
        self.totals_label.configure(
            text=(
                f"Keep: {summary.kept_count} files ({humanize.size(summary.kept_bytes)})\n"
                f"Drop: {summary.dropped_count} files ({humanize.size(summary.dropped_bytes)})\n"
                f"Cloud-only skipped: {summary.placeholder_count}"
            )
        )

        for child in self.category_frame.winfo_children():
            child.destroy()
        for cat, (count, total) in sorted(summary.by_category.items(), key=lambda kv: -kv[1][1]):
            row = ctk.CTkLabel(
                self.category_frame,
                text=f"{cat:<10} {count:>6} files   {humanize.size(total)}",
                font=theme.body_font(11),
                text_color=theme.TEXT,
                anchor="w",
            )
            row.pack(fill="x", pady=1)
