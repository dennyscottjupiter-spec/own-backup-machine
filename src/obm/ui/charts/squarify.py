# ---
# purpose: squarified treemap layout -- pure geometry, zero tkinter imports
# exports: Rect, squarify()
# gotcha: values are scaled to the rect's area internally; zero/negative values floor at 1
#         before scaling so a 0-byte file still gets a visible sliver, not a division by zero
# ---
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Rect:
    x: float
    y: float
    w: float
    h: float


def _worst(row_sum: float, row_max: float, row_min: float, side: float) -> float:
    if row_sum <= 0 or side <= 0 or row_min <= 0:
        return float("inf")
    return max(
        (side * side * row_max) / (row_sum * row_sum),
        (row_sum * row_sum) / (side * side * row_min),
    )


def _layout_row(row: list[float], rect: Rect) -> list[Rect]:
    s = sum(row)
    rects: list[Rect] = []
    if s <= 0 or rect.w <= 0 or rect.h <= 0:
        return [Rect(rect.x, rect.y, 0, 0) for _ in row]

    if rect.w >= rect.h:
        row_w = s / rect.h
        y = rect.y
        for v in row:
            h = (v / s) * rect.h
            rects.append(Rect(rect.x, y, row_w, h))
            y += h
    else:
        row_h = s / rect.w
        x = rect.x
        for v in row:
            w = (v / s) * rect.w
            rects.append(Rect(x, rect.y, w, row_h))
            x += w
    return rects


def _shrink(rect: Rect, row_sum: float) -> Rect:
    if rect.w >= rect.h:
        used = row_sum / rect.h if rect.h else 0.0
        used = min(used, rect.w)
        return Rect(rect.x + used, rect.y, rect.w - used, rect.h)
    used = row_sum / rect.w if rect.w else 0.0
    used = min(used, rect.h)
    return Rect(rect.x, rect.y + used, rect.w, rect.h - used)


def _squarify_scaled(values: list[float], rect: Rect) -> list[Rect]:
    # Running sum/max/min turn each _worst() check into O(1) instead of re-scanning the
    # whole row -- with hundreds of near-uniform-sized items in one row (a real directory
    # listing) the naive re-scan version is O(n^2) per node and dominates layout time.
    result: list[Rect] = []
    remaining = rect
    row: list[float] = []
    row_sum = 0.0
    row_max = 0.0
    row_min = float("inf")
    i = 0
    n = len(values)

    while i < n:
        side = min(remaining.w, remaining.h)
        v = values[i]
        new_sum = row_sum + v
        new_max = max(row_max, v)
        new_min = min(row_min, v)

        if not row or _worst(new_sum, new_max, new_min, side) <= _worst(row_sum, row_max, row_min, side):
            row.append(v)
            row_sum, row_max, row_min = new_sum, new_max, new_min
            i += 1
        else:
            result.extend(_layout_row(row, remaining))
            remaining = _shrink(remaining, row_sum)
            row = []
            row_sum = 0.0
            row_max = 0.0
            row_min = float("inf")

    if row:
        result.extend(_layout_row(row, remaining))
    return result


def squarify(values: list[float], rect: Rect) -> list[Rect]:
    if not values or rect.w <= 0 or rect.h <= 0:
        return []
    floored = [max(v, 1.0) for v in values]
    area = rect.w * rect.h
    total = sum(floored)
    scale = area / total
    scaled = [v * scale for v in floored]
    return _squarify_scaled(scaled, rect)
