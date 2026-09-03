# ---
# purpose: selected/deselected/dropped donut, the back-up-only-these-kinds selector with an
#          all-at-once toggle, and a per-category size bar chart -- all of which track what is
#          still ticked, not just what the scan kept
# exports: SummaryPanel
# depends: pipeline/aggregate.py, charts/{bar_chart,donut_chart}, ui/{panel_header,type_filter}
# gotcha: the Select all label must describe what the NEXT press does, so it is recomputed both
#         after a scan and after every press.
#         refresh_selection() must never call update_result(): that rebuilds the type filter rows,
#         and rebuilding them from a checkbox command destroys the widget that fired it. It is also
#         debounced, because build_summary() walks every candidate on the Tk thread.
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
SELECT_ALL = "Select all"
SELECT_NONE = "Select none"
SELECTION_DEBOUNCE_MS = 250

# selected keeps the accent, the give-up slice greys out, dropped stays the danger red
DONUT_COLORS = [theme.ACCENT, theme.MUTED, theme.DANGER]


class SummaryPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, on_expand=None, on_selection_change=None) -> None:
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)

        header = panel_header.build(self, "Summary", on_expand)
        self.select_button = ctk.CTkButton(
            header, text=SELECT_ALL, width=88, height=24, fg_color=theme.ACCENT,
            font=theme.body_font(11), command=self._toggle_all,
        )
        self.select_button.pack(side="right", padx=(4, 8))

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

        ctk.CTkLabel(
            content, text="Back up only these kinds  —  \"list\" shows what is in one",
            font=theme.body_font(11),
            text_color=theme.MUTED,
        ).pack(
            anchor="w", padx=16, pady=(8, 0)
        )
        self._on_selection_change = on_selection_change
        self.type_filter = TypeFilter(content, on_change=self._selection_changed)
        self.type_filter.pack(fill="x", padx=12, pady=(2, 0))

        ctk.CTkLabel(content, text="By category (size)", font=theme.body_font(11), text_color=theme.MUTED).pack(
            anchor="w", padx=16, pady=(8, 0)
        )
        self.bar_chart = BarChart(content, height=BAR_CHART_HEIGHT)
        self.bar_chart.pack(fill="x", padx=8, pady=8)

        self._result: DryRunResult | None = None
        self._selection_job: str | None = None

    def _toggle_all(self) -> None:
        """One button: first press selects every category, the next press clears them all."""
        self.type_filter.set_all(not self.type_filter.all_selected())

    def _selection_changed(self) -> None:
        # any change -- one checkbox or the whole lot -- can flip what the button should do next
        self._sync_select_label()
        self._schedule_charts()
        if self._on_selection_change is not None:
            self._on_selection_change()

    def _sync_select_label(self) -> None:
        self.select_button.configure(text=SELECT_NONE if self.type_filter.all_selected() else SELECT_ALL)

    def refresh_selection(self) -> None:
        """Selection changed somewhere else (a big-file row) -- re-read the records into the
        checkboxes and the charts, without rebuilding any row."""
        self.type_filter.refresh_selection()
        self._sync_select_label()
        self._schedule_charts()

    def _schedule_charts(self) -> None:
        if self._selection_job is not None:
            self.after_cancel(self._selection_job)
        self._selection_job = self.after(SELECTION_DEBOUNCE_MS, self._draw_charts)

    def update_result(self, result: DryRunResult) -> None:
        self._result = result
        self.type_filter.update_result(result)
        self._sync_select_label()
        self._draw_charts()

    def _draw_charts(self) -> None:
        self._selection_job = None
        if self._result is None:
            return
        summary = build_summary(self._result.candidates, self._result.issues)
        given_up = summary.kept_bytes - summary.selected_bytes
        self.totals_label.configure(
            text=(
                f"Selected: {humanize.count(summary.selected_count)} files "
                f"({humanize.size(summary.selected_bytes)})\n"
                f"Of kept: {humanize.count(summary.kept_count)} files ({humanize.size(summary.kept_bytes)})\n"
                f"Drop: {humanize.count(summary.dropped_count)} files ({humanize.size(summary.dropped_bytes)})\n"
                f"Cloud-only skipped: {humanize.count(summary.placeholder_count)}"
            )
        )
        self.donut.update_data(
            [
                ("selected", summary.selected_bytes),
                ("deselected", given_up),
                ("drop", summary.dropped_bytes),
            ],
            colors=DONUT_COLORS,
        )
        self.bar_chart.update_data(
            [(cat, total) for cat, (_, total) in summary.by_category.items()],
            selected={cat: total for cat, (_, total) in summary.by_category_selected.items()},
        )
