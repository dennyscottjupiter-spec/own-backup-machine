# ---
# purpose: the plain-text index written INSIDE every archive -- what is in it, in which folders,
#          without extracting or clicking through anything
# exports: README_NAME, build(), write_temp()
# depends: models.CandidateFile, humanize.py, archive/{tree,readme_html,manifest}.py
# gotcha: pure text assembly, no filesystem reads -- sizes come from the already-scanned
#         CandidateFile records, so this stays correct for files that vanished after the scan
# ---
from __future__ import annotations

import os
import tempfile
from datetime import datetime

from .. import humanize
from ..models import CandidateFile
from . import tree as tree_mod
from .manifest import MANIFEST_SUFFIX
from .readme_html import HTML_NAME

README_NAME = "BACKUP-README.txt"

_WHAT_THIS_IS = """WHAT THIS IS
  A delta backup: only the files that changed since the previous run, with their original
  folder structure preserved. Extract the whole archive to restore a path exactly where it
  came from, or pull a single file out of it -- the folder layout below mirrors the archive."""

COLUMN = 58


def _files_label(n: int) -> str:
    return f"{humanize.count(n)} file" + ("" if n == 1 else "s")


def _pad(label: str) -> str:
    """Keep the totals in a column, but never let a long folder name touch them."""
    return label.ljust(COLUMN) if len(label) < COLUMN else label + "  "


def _render_tree(node: tree_mod.Node, depth: int, lines: list[str]) -> None:
    for name, child in tree_mod.sorted_kids(node):
        parts, kid = tree_mod.collapse_chain(name, child)
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
    lines = ["WHAT KIND OF FILES"]
    for category, count, total in tree_mod.by_kind(files):
        lines.append(f"  {category:<14}{_files_label(count):>12}   {humanize.size(total)}")
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
        _render_tree(tree_mod.build_tree(ordered), 0, lines)
    else:
        lines.append("  (nothing was archived in this run)")
    lines.append("")

    lines.append("EVERY FILE IN THIS ARCHIVE")
    for f in ordered:
        lines.append(f"  [{humanize.size(f.size)}]".ljust(16) + f.path)
    lines.append("")

    lines.append("ALSO WRITTEN")
    lines.append(f"  {HTML_NAME} -- in this archive: the same index as a searchable page.")
    lines.append(f"  {archive_name}{MANIFEST_SUFFIX} -- next to the archive: the listing as JSON,")
    lines.append("      plus every scan issue.")
    return "\n".join(lines) + "\n"


def write_temp(text: str, name: str = README_NAME) -> str:
    """Drop the text in a temp folder under its real name -- the archivers store the basename."""
    path = os.path.join(tempfile.mkdtemp(prefix="obm_readme_"), name)
    newline = "\r\n" if name.endswith(".txt") else "\n"
    with open(path, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)
    return path
