# ---
# purpose: one colour per file category, shared by the dashboard charts and the HTML archive index
# exports: CATEGORY_COLORS, color_for_category(), dim()
# gotcha: lives outside ui/ on purpose -- archive/ needs these colours and nothing outside ui/
#         may import from ui/
# ---
from __future__ import annotations

CATEGORY_COLORS = {
    "document": "#3b82f6",
    "photo": "#22c55e",
    "video": "#ef4444",
    "audio": "#f59e0b",
    "code": "#8b5cf6",
    "archive": "#06b6d4",
    "program": "#ec4899",
    "llm model": "#14b8a6",
    "unknown": "#6b7280",
    "filtered": "#7f1d1d",
}


def color_for_category(category: str) -> str:
    return CATEGORY_COLORS.get(category, CATEGORY_COLORS["unknown"])


def dim(color: str, factor: float = 0.32) -> str:
    """The same hue, darkened toward the dark panel background -- how a deselected thing reads:
    still there, still identifiable by colour, visibly not part of the total any more."""
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"
