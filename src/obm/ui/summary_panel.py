# ---
# purpose: keep/drop/placeholder donut, the back-up-only-these-kinds selector, and a per-category
#          size bar chart, all refreshed after every scan
# exports: SummaryPanel
# depends: pipeline/aggregate.py, charts/{bar_chart,donut_chart}, ui/{panel_header,type_filter}
# ---
from __future__ import annotations

import customtkinter as ctk

from .. import humanize
from ..models import DryRunResult
from ..pipeline.aggregate import build_summary
from . import panel_header, theme
from .charts.bar_chart import BarChart
from .charts.donut_chart import DonutChart
from .type_filter import TypeFilter

BAR_CHART_HEIGHT = 130


class SummaryPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, on_expand=None, on_selection_change=None) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)

        panel_header.build(self, "Summary", on_expand)

        # the donut + filter + chart stack is taller than the tile ever gets on a laptop screen,
        # so the panel body scrolls instead of silently clipping whatever sits at the bottom
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)

        top = ctk.CTkFrame(content, fg_color="transparent")
        top.pack(fill="x", padx=8)

        self.donut = DonutChart(top, size=120)
        self.donut.pack(side="left", padx=8, pady=4)

        self.totals_label = ctk.CTkLabel(
            top, text="Scanning...", font=theme.body_font(), text_color=theme.TEXT, justify="left"
        )
        self.totals_label.pack(side="left", padx=8, anchor="center")

        ctk.CTkLabel(content, text="Back up only these kinds", font=theme.body_font(11), text_color=theme.MUTED).pack(
            anchor="w", padx=16, pady=(8, 0)
        )
        self.type_filter = TypeFilter(content, on_change=on_selection_change)
        self.type_filter.pack(fill="x", padx=12, pady=(2, 0))

        ctk.CTkLabel(content, text="By category (size)", font=theme.body_font(11), text_color=theme.MUTED).pack(
            anchor="w", padx=16, pady=(8, 0)
        )
        self.bar_chart = BarChart(content, height=BAR_CHART_HEIGHT)
        self.bar_chart.pack(fill="x", padx=8, pady=8)

    def update_result(self, result: DryRunResult) -> None:
        summary = build_summary(result.candidates, result.issues)
        self.totals_label.configure(
            text=(
                f"Keep: {humanize.count(summary.kept_count)} files ({humanize.size(summary.kept_bytes)})\n"
                f"Drop: {humanize.count(summary.dropped_count)} files ({humanize.size(summary.dropped_bytes)})\n"
                f"Cloud-only skipped: {humanize.count(summary.placeholder_count)}"
            )
        )
        self.type_filter.update_result(result)
        self.donut.update_data([
            ("keep", summary.kept_bytes),
            ("drop", summary.dropped_bytes),
        ])
        self.bar_chart.update_data([(cat, total) for cat, (_, total) in summary.by_category.items()])
