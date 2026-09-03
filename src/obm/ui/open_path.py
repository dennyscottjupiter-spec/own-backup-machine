# ---
# purpose: open a finished archive, or its folder with the archive already highlighted
# exports: open_containing_folder(), open_file()
# gotcha: explorer.exe exits 1 even when it worked, so its return code is deliberately ignored --
#         and "/select," takes no space before the path or Explorer opens Documents instead
# ---
from __future__ import annotations

import os
import subprocess


def open_containing_folder(path: str) -> None:
    subprocess.Popen(["explorer", f"/select,{os.path.normpath(path)}"])


def open_file(path: str) -> None:
    os.startfile(path)  # whatever is registered for .7z / .rar / .zip
