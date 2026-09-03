# ---
# purpose: flat candidate list -> directory tree with subtree byte sums, sorted descending once
# exports: TreeNode, build_tree()
# depends: models.CandidateFile, filter/classify.category_of
# gotcha: children are sorted by size descending HERE, once, so repeated relayouts on resize
#         never have to re-sort the same subtree.
#         selected_only reads CandidateFile.selected, which the Summary type filter mutates in
#         place -- so the tree has to be rebuilt after a selection change, not just relaid out.
# ---
from __future__ import annotations

from dataclasses import dataclass, field

from ...filter.classify import category_of
from ...models import CandidateFile


@dataclass(slots=True)
class TreeNode:
    name: str
    path: str
    is_dir: bool
    size: int = 0
    category: str = ""
    children: list["TreeNode"] = field(default_factory=list)


def build_tree(
    candidates: list[CandidateFile], include_dropped: bool = False, selected_only: bool = False
) -> TreeNode:
    root = TreeNode(name="", path="", is_dir=True)
    index: dict[str, TreeNode] = {"": root}

    for c in candidates:
        if "placeholder" in c.tags:
            continue
        if c.verdict == "keep":
            if selected_only and not c.selected:
                continue
        elif not include_dropped:
            continue

        parts = [p for p in c.path.replace("/", "\\").split("\\") if p]
        if not parts:
            continue

        parent = root
        parent_key = ""
        for part in parts[:-1]:
            key = f"{parent_key}\\{part.lower()}" if parent_key else part.lower()
            node = index.get(key)
            if node is None:
                node = TreeNode(name=part, path=(f"{parent.path}\\{part}" if parent.path else part), is_dir=True)
                parent.children.append(node)
                index[key] = node
            parent = node
            parent_key = key

        category = "filtered" if c.verdict == "drop" else category_of(c.path)
        parent.children.append(TreeNode(name=parts[-1], path=c.path, is_dir=False, size=c.size, category=category))

    _finalize(root)
    return root


def _finalize(node: TreeNode) -> int:
    if not node.is_dir:
        return node.size
    total = sum(_finalize(child) for child in node.children)
    node.size = total
    node.children.sort(key=lambda n: n.size, reverse=True)
    return total
