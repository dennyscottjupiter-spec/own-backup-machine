# ---
# purpose: keep/drop/placeholder donut + per-category size bar chart, refreshed after every scan
# exports: SummaryPanel
# depends: pipeline/aggregate.py, charts/{bar_chart,donut_chart}
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import humanize
from ..models import DryRunResult
from ..pipeline.aggregate import build_summary
from . import theme
from .charts.bar_chart import BarChart
from .charts.donut_chart import DonutChart


class SummaryPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)

        heading = ctk.CTkLabel(self, text="Summary", font=theme.heading_font(), text_color=theme.TEXT)
        heading.pack(anchor="w", padx=16, pady=(12, 4))

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=8)

        self.donut = DonutChart(top, size=120)
        self.donut.pack(side="left", padx=8, pady=4)

        self.totals_label = ctk.CTkLabel(
            top, text="Scanning...", font=theme.body_font(), text_color=theme.TEXT, justify="left"
        )
        self.totals_label.pack(side="left", padx=8, anchor="center")

        ctk.CTkLabel(self, text="By category (size)", font=theme.body_font(11), text_color=theme.MUTED).pack(
            anchor="w", padx=16, pady=(8, 0)
        )
        self.bar_chart = BarChart(self)
        self.bar_chart.pack(fill="both", expand=True, padx=8, pady=8)

    def update_result(self, result: DryRunResult) -> None:
        summary = build_summary(result.candidates, result.issues)
        self.totals_label.configure(
            text=(
                f"Keep: {summary.kept_count} files ({humanize.size(summary.kept_bytes)})\n"
                f"Drop: {summary.dropped_count} files ({humanize.size(summary.dropped_bytes)})\n"
                f"Cloud-only skipped: {summary.placeholder_count}"
            )
        )
        self.donut.update_data([
            ("keep", summary.kept_bytes),
            ("drop", summary.dropped_bytes),
        ])
        self.bar_chart.update_data([(cat, total) for cat, (_, total) in summary.by_category.items()])
