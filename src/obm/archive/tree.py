# ---
# purpose: the archived-files folder tree, shared by the text and HTML indexes
# exports: Node, build_tree(), collapse_chain(), sorted_kids(), by_kind()
# depends: models.CandidateFile, filter/classify.py
# gotcha: pure assembly over already-scanned records -- never touches the filesystem, so it stays
#         correct for files that vanished between the scan and the archive
# ---
from __future__ import annotations

import os
from collections import Counter

from ..filter.classify import category_of
from ..models import CandidateFile


class Node:
    __slots__ = ("kids", "count", "size", "direct")

    def __init__(self) -> None:
        self.kids: dict[str, Node] = {}
        self.count = 0
        self.size = 0
        self.direct = 0  # files sitting in THIS folder -- what stops a chain being collapsed


def folder_parts(path: str) -> list[str]:
    return os.path.dirname(path).replace("/", "\\").split("\\")


def build_tree(files: list[CandidateFile]) -> Node:
    root = Node()
    for f in files:
        node = root
        node.count += 1
        node.size += f.size
        for part in folder_parts(f.path):
            node = node.kids.setdefault(part, Node())
            node.count += 1
            node.size += f.size
        node.direct += 1
    return root


def sorted_kids(node: Node) -> list[tuple[str, Node]]:
    return sorted(node.kids.items(), key=lambda kv: (-kv[1].size, kv[0].lower()))


def collapse_chain(name: str, node: Node) -> tuple[list[str], Node]:
    """A folder that only ever leads to one other folder is joined onto it -- the whole point is
    not having to walk C:\\ -> Users -> name -> AppData one level at a time."""
    parts = [name]
    while len(node.kids) == 1 and node.direct == 0:
        (only_name, only_kid), = node.kids.items()
        parts.append(only_name)
        node = only_kid
    return parts, node


def by_kind(files: list[CandidateFile]) -> list[tuple[str, int, int]]:
    """(category, file count, bytes), biggest first."""
    counts: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    for f in files:
        category = category_of(f.path)
        counts[category] += 1
        sizes[category] += f.size
    return [(cat, counts[cat], total) for cat, total in sizes.most_common()]
