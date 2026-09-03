# ---
# purpose: the plain-text index written INSIDE every archive -- what is in it, in which folders,
#          without extracting or clicking through anything
# exports: README_NAME, build(), write_temp()
# depends: models.CandidateFile, humanize.py, filter/classify.py, archive/manifest.py
# gotcha: pure text assembly, no filesystem reads -- sizes come from the already-scanned
#         CandidateFile records, so this stays correct for files that vanished after the scan
# ---
from __future__ import annotations

import os
import tempfile
from collections import Counter
from datetime import datetime

from .. import humanize
from ..filter.classify import category_of
from ..models import CandidateFile
from .manifest import MANIFEST_SUFFIX

README_NAME = "BACKUP-README.txt"

_WHAT_THIS_IS = """WHAT THIS IS
  A delta backup: only the files that changed since the previous run, with their original
  folder structure preserved. Extract the whole archive to restore a path exactly where it
  came from, or pull a single file out of it -- the folder layout below mirrors the archive."""


class _Node:
    __slots__ = ("kids", "count", "size", "direct")

    def __init__(self) -> None:
        self.kids: dict[str, _Node] = {}
        self.count = 0
        self.size = 0
        self.direct = 0  # files sitting in THIS folder -- what stops a chain being collapsed


def _folder_parts(path: str) -> list[str]:
    return os.path.dirname(path).replace("/", "\\").split("\\")


def _build_tree(files: list[CandidateFile]) -> _Node:
    root = _Node()
    for f in files:
        node = root
        node.count += 1
        node.size += f.size
        for part in _folder_parts(f.path):
            node = node.kids.setdefault(part, _Node())
            node.count += 1
            node.size += f.size
        node.direct += 1
    return root


COLUMN = 58


def _files_label(n: int) -> str:
    return f"{humanize.count(n)} file" + ("" if n == 1 else "s")


def _pad(label: str) -> str:
    """Keep the totals in a column, but never let a long folder name touch them."""
    return label.ljust(COLUMN) if len(label) < COLUMN else label + "  "


def _render_tree(node: _Node, depth: int, lines: list[str]) -> None:
    for name, kid in sorted(node.kids.items(), key=lambda kv: (-kv[1].size, kv[0].lower())):
        # a folder that only ever leads to one other folder is joined onto it: the whole point
        # is not having to walk C:\ -> Users -> name -> AppData one level at a time
        parts = [name]
        while len(kid.kids) == 1 and kid.direct == 0:
            (only_name, only_kid), = kid.kids.items()
            parts.append(only_name)
            kid = only_kid
        label = "  " * (depth + 1) + "\\".join(parts) + "\\"
        lines.append(_pad(label) + f"{_files_label(kid.count)}   {humanize.size(kid.size)}")
        _render_tree(kid, depth + 1, lines)


def _front_matter(archive_name: str, run_id: str, created: datetime, tool_label: str, files: list[CandidateFile]) -> list[str]:
    return [
        "---",
        f"archive:  {archive_name}",
        f"created:  {created.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"run id:   {run_id}",
        f"files:    {humanize.count(len(files))}",
        f"size:     {humanize.size(sum(f.size for f in files))} before compression",
        f"made by:  own-backup-machine, {tool_label}",
        "---",
        "",
    ]


def _by_kind(files: list[CandidateFile]) -> list[str]:
    counts: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    for f in files:
        category = category_of(f.path)
        counts[category] += 1
        sizes[category] += f.size

    lines = ["WHAT KIND OF FILES"]
    for category, total in sizes.most_common():
        lines.append(f"  {category:<14}{_files_label(counts[category]):>12}   {humanize.size(total)}")
    return lines


def build(
    archive_name: str,
    run_id: str,
    created: datetime,
    tool_label: str,
    files: list[CandidateFile],
) -> str:
    ordered = sorted(files, key=lambda f: f.path.lower())
    lines = _front_matter(archive_name, run_id, created, tool_label, ordered)
    lines.append(_WHAT_THIS_IS)
    lines.append("")
    lines.extend(_by_kind(ordered))
    lines.append("")

    lines.append("WHERE THE FILES CAME FROM")
    if ordered:
        _render_tree(_build_tree(ordered), 0, lines)
    else:
        lines.append("  (nothing was archived in this run)")
    lines.append("")

    lines.append("EVERY FILE IN THIS ARCHIVE")
    for f in ordered:
        lines.append(f"  [{humanize.size(f.size)}]".ljust(16) + f.path)
    lines.append("")

    lines.append("ALSO WRITTEN, NEXT TO THE ARCHIVE")
    lines.append(f"  {archive_name}{MANIFEST_SUFFIX} -- the same listing as JSON, plus every scan issue.")
    return "\n".join(lines) + "\n"


def write_temp(text: str) -> str:
    """Drop the text in a temp folder under its real name -- the archivers store the basename."""
    path = os.path.join(tempfile.mkdtemp(prefix="obm_readme_"), README_NAME)
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)
    return path
