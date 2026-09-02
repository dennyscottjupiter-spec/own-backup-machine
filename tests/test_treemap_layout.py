import time

from obm.ui.charts.squarify import Rect
from obm.ui.charts.treemap_layout import layout
from obm.ui.charts.treemap_model import TreeNode


def _synthetic_tree(num_dirs=200, files_per_dir=1000) -> TreeNode:
    root = TreeNode(name="", path="", is_dir=True)
    for d in range(num_dirs):
        dir_node = TreeNode(name=f"dir{d}", path=f"dir{d}", is_dir=True)
        for f in range(files_per_dir):
            size = ((d * files_per_dir + f) % 99_999) + 1
            dir_node.children.append(
                TreeNode(name=f"file{f}.txt", path=f"dir{d}/file{f}.txt", is_dir=False, size=size)
            )
        dir_node.children.sort(key=lambda n: n.size, reverse=True)
        dir_node.size = sum(c.size for c in dir_node.children)
        root.children.append(dir_node)
    root.children.sort(key=lambda n: n.size, reverse=True)
    root.size = sum(c.size for c in root.children)
    return root


def test_layout_of_200k_files_completes_under_500ms_and_caps_tile_count():
    root = _synthetic_tree(num_dirs=200, files_per_dir=1000)
    assert sum(len(d.children) for d in root.children) == 200_000

    started = time.perf_counter()
    tiles = layout(root, Rect(0, 0, 1200, 700))
    elapsed = time.perf_counter() - started

    assert elapsed < 0.5, f"layout took {elapsed:.3f}s, expected < 0.5s"
    assert len(tiles) < 3000, f"expected pruning to cap tile count, got {len(tiles)}"


def test_pruning_collapses_remainder_into_a_more_tile():
    root = TreeNode(name="", path="", is_dir=True)
    for i in range(500):
        root.children.append(TreeNode(name=f"f{i}.txt", path=f"f{i}.txt", is_dir=False, size=100))
    root.size = sum(c.size for c in root.children)

    tiles = layout(root, Rect(0, 0, 200, 200))  # small canvas -> most tiles fall below MIN_TILE_AREA
    more_tiles = [t for t in tiles if t.is_more]
    assert len(more_tiles) == 1
    assert more_tiles[0].more_count > 0


def test_more_tile_accounting_is_lossless_at_root_level():
    root = TreeNode(name="", path="", is_dir=True)
    for i in range(500):
        root.children.append(TreeNode(name=f"f{i}.txt", path=f"f{i}.txt", is_dir=False, size=i + 1))
    root.children.sort(key=lambda n: n.size, reverse=True)
    root.size = sum(c.size for c in root.children)

    tiles = layout(root, Rect(0, 0, 200, 200))
    depth1 = [t for t in tiles if t.depth == 1]

    total_size = sum(t.size for t in depth1)
    assert total_size == root.size

    real_count = sum(1 for t in depth1 if not t.is_more)
    more_count = sum(t.more_count for t in depth1 if t.is_more)
    assert real_count + more_count == len(root.children)


def test_no_children_produces_no_tiles():
    root = TreeNode(name="", path="", is_dir=True)
    assert layout(root, Rect(0, 0, 100, 100)) == []


def test_zero_size_rect_produces_no_tiles():
    root = TreeNode(name="", path="", is_dir=True)
    root.children.append(TreeNode(name="f.txt", path="f.txt", is_dir=False, size=10))
    assert layout(root, Rect(0, 0, 0, 100)) == []
