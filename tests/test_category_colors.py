from obm.filter.rules import CATEGORIES
from obm.ui.charts.canvas_base import CATEGORY_COLORS


def test_every_category_has_a_chart_color():
    missing = sorted(set(CATEGORIES) - set(CATEGORY_COLORS))
    assert missing == [], f"categories with no color, they would all draw grey: {missing}"


def test_fallback_keys_exist():
    # drawn for files no category claims, and for blocklisted files in the treemap
    assert "unknown" in CATEGORY_COLORS
    assert "filtered" in CATEGORY_COLORS
