import random
import statistics

import pytest

from obm.ui.charts.squarify import Rect, squarify


def _aspect_ratios(rects):
    ratios = []
    for r in rects:
        if r.w <= 0 or r.h <= 0:
            continue
        ratios.append(max(r.w / r.h, r.h / r.w))
    return ratios


@pytest.mark.parametrize("seed", range(10))
def test_areas_sum_to_rect_no_overlap_all_inside_bounds(seed):
    rng = random.Random(seed)
    values = [rng.randint(1, 1_000_000) for _ in range(rng.randint(1, 60))]
    rect = Rect(0, 0, 1200, 700)

    rects = squarify(values, rect)
    assert len(rects) == len(values)

    total_area = sum(r.w * r.h for r in rects)
    assert total_area == pytest.approx(rect.w * rect.h, rel=1e-6)

    for r in rects:
        assert r.x >= rect.x - 1e-6
        assert r.y >= rect.y - 1e-6
        assert r.x + r.w <= rect.x + rect.w + 1e-6
        assert r.y + r.h <= rect.y + rect.h + 1e-6

    ratios = _aspect_ratios(rects)
    if ratios:
        assert statistics.median(ratios) < 3


def test_empty_values_returns_empty():
    assert squarify([], Rect(0, 0, 100, 100)) == []


def test_zero_area_rect_returns_empty():
    assert squarify([1, 2, 3], Rect(0, 0, 0, 100)) == []


def test_single_value_fills_whole_rect():
    rects = squarify([42], Rect(0, 0, 200, 100))
    assert len(rects) == 1
    r = rects[0]
    assert r.w == pytest.approx(200)
    assert r.h == pytest.approx(100)


def test_zero_value_items_still_get_a_rect():
    rects = squarify([0, 0, 1000], Rect(0, 0, 100, 100))
    assert len(rects) == 3
    for r in rects:
        assert r.w >= 0 and r.h >= 0
