import pathlib
import re

SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "obm"
IMPORT_UI_RE = re.compile(r"^\s*(from\s+\.{1,3}ui(\.|.\s+import)|from\s+obm\.ui\b|import\s+obm\.ui\b)")


def test_nothing_outside_ui_imports_from_ui():
    offenders = []
    for path in SRC.rglob("*.py"):
        if "ui" in path.relative_to(SRC).parts[:1]:
            continue  # ui/ may import from anything, including itself
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if IMPORT_UI_RE.match(line):
                offenders.append(f"{path.relative_to(SRC)}:{lineno}: {line.strip()}")

    assert offenders == [], "modules outside ui/ must never import from ui/:\n" + "\n".join(offenders)
