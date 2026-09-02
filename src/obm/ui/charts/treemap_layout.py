# ---
# purpose: prune + squarify a TreeNode into a flat list[Tile] -- runs on the worker thread
# exports: Tile, layout()
# depends: squarify.py, treemap_model.TreeNode
# gotcha: pruning at 600px^2 / depth 6 caps output at ~1000-1500 tiles regardless of input size --
#         this, not the drawing code, is what keeps a 100k-file dataset from freezing the canvas
# ---
from __future__ import annotations

from dataclasses import dataclass

from .squarify import Rect, squarify
from .treemap_model import TreeNode

MIN_TILE_AREA = 600.0
MAX_DEPTH = 6
HEADER_HEIGHT = 18.0


@dataclass(slots=True)
class Tile:
    rect: Rect
    label: str
    path: str
    category: str
    size: int
    is_dir: bool
    depth: int
    is_more: bool = False
    more_count: int = 0


def layout(node: TreeNode, rect: Rect) -> list["Tile"]:
    tiles: list[Tile] = []
    _layout_node(node, rect, depth=0, tiles=tiles)
    return tiles


def _leftover_tile(node: TreeNode, rect: Rect, depth: int, count: int, size: int) -> Tile:
    return Tile(
        rect=rect, label=f"+{count} more", path=node.path, category="",
        size=size, is_dir=False, depth=depth, is_more=True, more_count=count,
    )


def _layout_node(node: TreeNode, rect: Rect, depth: int, tiles: list[Tile]) -> None:
    if not node.children or rect.w <= 0 or rect.h <= 0:
        return

    header = HEADER_HEIGHT if (node.is_dir and 0 < depth <= 2) else 0.0
    content = Rect(rect.x, rect.y + header, rect.w, max(rect.h - header, 0.0))
    if content.w <= 0 or content.h <= 0:
        return

    if depth >= MAX_DEPTH:
        tiles.append(_leftover_tile(node, content, depth + 1, len(node.children), node.size))
        return

    # Feeding all of node.children into squarify() is O(n) per node -- fine once, but a
    # directory with thousands of files at a tiny on-screen area would still burn the full
    # n just to discover almost every rect lands below MIN_TILE_AREA. Cap the input to
    # roughly how many tiles the area can possibly hold, and fold the (already
    # size-sorted-descending) remainder into one synthetic "leftover" value so squarify
    # still gives it a real, correctly-proportioned rectangle.
    area = content.w * content.h
    budget = max(1, int(area / MIN_TILE_AREA) + 8)

    children = node.children
    if len(children) > budget:
        head = children[:budget]
        tail = children[budget:]
    else:
        head = children
        tail = []

    sizes = [c.size for c in head]
    tail_size = sum(c.size for c in tail)
    if tail:
        sizes.append(tail_size)

    rects = squarify(sizes, content)
    if not rects:
        return

    cutoff = len(head)
    for i, r in enumerate(rects[: len(head)]):
        if r.w * r.h < MIN_TILE_AREA:
            cutoff = i
            break

    for child, child_rect in zip(head[:cutoff], rects[:cutoff]):
        tiles.append(Tile(
            rect=child_rect, label=child.name, path=child.path, category=child.category,
            size=child.size, is_dir=child.is_dir, depth=depth + 1,
        ))
        if child.is_dir:
            _layout_node(child, child_rect, depth + 1, tiles)

    collapsed = head[cutoff:]
    collapsed_count = len(collapsed) + len(tail)
    if collapsed_count == 0:
        return

    collapsed_size = sum(c.size for c in collapsed) + tail_size
    if not collapsed:
        # only the synthetic tail item was collapsed -- it already has its own real rect
        collapsed_rect = rects[len(head)]
    else:
        tail_rects = rects[len(head):] if tail else []
        collapsed_rect = _bounding_union(rects[cutoff:len(head)] + tail_rects)

    tiles.append(_leftover_tile(node, collapsed_rect, depth + 1, collapsed_count, collapsed_size))


def _bounding_union(rects: list[Rect]) -> Rect:
    x0 = min(r.x for r in rects)
    y0 = min(r.y for r in rects)
    x1 = max(r.x + r.w for r in rects)
    y1 = max(r.y + r.h for r in rects)
    return Rect(x0, y0, x1 - x0, y1 - y0)
