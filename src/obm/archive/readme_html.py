# ---
# purpose: BACKUP-README.html -- the same index as the text one, as one offline page you can
#          search and fold open
# exports: HTML_NAME, FILE_ROW_CAP, build()
# depends: archive/{tree,report_style,manifest}.py, humanize.py, filter/classify.py, palette.py
# gotcha: the flat file list is capped at FILE_ROW_CAP rows -- a 200k-row DOM freezes a browser,
#         and the .txt next to it is the uncapped listing
# ---
from __future__ import annotations

from datetime import datetime
from html import escape

from .. import humanize
from ..filter.classify import category_of
from ..models import CandidateFile
from ..palette import CATEGORY_COLORS
from . import tree as tree_mod
from .manifest import MANIFEST_SUFFIX
from .report_style import page

HTML_NAME = "BACKUP-README.html"
FILE_ROW_CAP = 5000

FOLDER_TONE = "#3b82f6"


def _files_label(n: int) -> str:
    return f"{humanize.count(n)} file" + ("" if n == 1 else "s")


def _share(part: int, whole: int) -> float:
    return 100.0 * part / whole if whole else 0.0


def _folder_cells(label: str, count: int, size: int) -> str:
    return (
        f'<i class="fill"></i><span class="label">{escape(label)}</span>'
        f'<span class="n">{_files_label(count)}</span><span class="sz">{humanize.size(size)}</span>'
    )


OPEN_DEPTH = 2  # deep enough to land past C:\Users\<name>\ without unfolding the whole disk


def _tree_html(node: tree_mod.Node, prefix: str, out: list[str], depth: int = 0) -> None:
    for name, child in tree_mod.sorted_kids(node):
        parts, kid = tree_mod.collapse_chain(name, child)
        label = "\\".join(parts) + "\\"
        path = escape((prefix + label).lower(), quote=True)
        style = f'--w:{_share(kid.size, node.size):.4g};--tone:{FOLDER_TONE}'
        cells = _folder_cells(label, kid.count, kid.size)

        if not kid.kids:
            out.append(f'<div class="row" data-p="{path}" style="{style}">{cells}</div>')
            continue

        opened = " open" if depth < OPEN_DEPTH else ""
        out.append(f'<details class="node" data-p="{path}"{opened}>')
        out.append(f'<summary style="{style}">{cells}</summary>')
        out.append('<div class="kids">')
        _tree_html(kid, prefix + label, out, depth + 1)
        out.append("</div></details>")


def _kinds_html(files: list[CandidateFile]) -> str:
    kinds = tree_mod.by_kind(files)
    total = sum(size for _, _, size in kinds)

    bar = "".join(
        f'<span style="flex:{size or 1};background:{CATEGORY_COLORS.get(cat, CATEGORY_COLORS["unknown"])}"'
        f' title="{escape(cat, quote=True)}"></span>'
        for cat, _, size in kinds
    )
    rows = "".join(
        f'<tr><td><i class="swatch" style="background:'
        f'{CATEGORY_COLORS.get(cat, CATEGORY_COLORS["unknown"])}"></i>{escape(cat)}</td>'
        f'<td>{_files_label(count)}</td><td>{humanize.size(size)}</td>'
        f'<td class="num">{_share(size, total):.0f}%</td></tr>'
        for cat, count, size in kinds
    )
    return f'<div class="share">{bar}</div><table class="kinds"><tbody>{rows}</tbody></table>'


def _files_html(files: list[CandidateFile]) -> str:
    # no size bar here: one 900 MB file next to a 2 KB one renders every other bar as nothing
    rows = []
    for f in files[:FILE_ROW_CAP]:
        tone = CATEGORY_COLORS.get(category_of(f.path), CATEGORY_COLORS["unknown"])
        rows.append(
            f'<div class="row" data-p="{escape(f.path.lower(), quote=True)}">'
            f'<i class="dot" style="background:{tone}"></i>'
            f'<span class="label">{escape(f.path)}</span>'
            f'<span class="sz">{humanize.size(f.size)}</span></div>'
        )
    html = f'<div class="tree files">{"".join(rows)}</div>'
    if len(files) > FILE_ROW_CAP:
        rest = len(files) - FILE_ROW_CAP
        html += (
            f'<p class="cut">{humanize.count(FILE_ROW_CAP)} of {humanize.count(len(files))} files are '
            f"listed here, largest first. The other {humanize.count(rest)} are in BACKUP-README.txt "
            "inside this archive, and in the .json manifest next to it.</p>"
        )
    return html


def _ledger(run_id: str, created: datetime, tool_label: str, files: list[CandidateFile]) -> str:
    pairs = [
        ("Files", humanize.count(len(files))),
        ("Size before compression", humanize.size(sum(f.size for f in files))),
        ("Created", created.strftime("%Y-%m-%d %H:%M UTC")),
        ("Run", run_id),
        ("Made by", f"obm, {tool_label}"),
    ]
    return "".join(f"<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>" for k, v in pairs)


def build(
    archive_name: str,
    run_id: str,
    created: datetime,
    tool_label: str,
    files: list[CandidateFile],
) -> str:
    by_path = sorted(files, key=lambda f: f.path.lower())
    by_size = sorted(files, key=lambda f: (-f.size, f.path.lower()))

    if by_path:
        tree: list[str] = []
        _tree_html(tree_mod.build_tree(by_path), "", tree)
        tree_html = f'<div class="tree">{"".join(tree)}</div>'
        kinds_html = _kinds_html(by_path)
        files_html = _files_html(by_size)
    else:
        tree_html = '<p class="empty">This run archived nothing.</p>'
        kinds_html = ""
        files_html = ""

    return page(
        title=escape(archive_name),
        ledger=_ledger(run_id, created, tool_label, by_path),
        kinds=kinds_html,
        tree=tree_html,
        files=files_html,
        manifest_name=escape(archive_name + MANIFEST_SUFFIX),
    )
