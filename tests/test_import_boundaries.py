import pathlib
import re

SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "obm"
IMPORT_UI_RE = re.compile(
    r"^\s*(from\s+\.{1,3}ui(\.\S+)?\s+import|from\s+\.{1,3}\s*import\s+ui\b"
    r"|from\s+obm\.ui\b|import\s+obm\.ui\b)"
)


# the CLI entry point is the composition root -- it is the one module allowed to reach for the
# GUI, and it does so inside main() so a headless --run never imports tkinter at all
ENTRY_POINT = "__main__.py"


def test_nothing_outside_ui_imports_from_ui():
    offenders = []
    for path in SRC.rglob("*.py"):
        if "ui" in path.relative_to(SRC).parts[:1] or path.name == ENTRY_POINT:
            continue  # ui/ may import from anything, including itself
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if IMPORT_UI_RE.match(line):
                offenders.append(f"{path.relative_to(SRC)}:{lineno}: {line.strip()}")

    assert offenders == [], "modules outside ui/ must never import from ui/:\n" + "\n".join(offenders)
