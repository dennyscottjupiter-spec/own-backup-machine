# ---
# purpose: edit config.toml -- destination, extra roots/excludes, USN toggle, archive/UI knobs
# exports: open_settings_dialog()
# depends: config.py
# ---
from __future__ import annotations

import tkinter.filedialog as filedialog
from typing import Callable

import customtkinter as ctk

from .. import config as config_mod
from . import theme


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, cfg: config_mod.Config, on_saved: Callable[[config_mod.Config], None]) -> None:
        super().__init__(master)
        self.title("Settings")
        self.geometry("520x600")
        self.configure(fg_color=theme.BG)
        self._on_saved = on_saved

        self._dest_var = ctk.StringVar(value=cfg.destination_path)
        self._usn_var = ctk.BooleanVar(value=cfg.use_usn)
        self._level_var = ctk.StringVar(value=str(cfg.archive_level))
        self._hash_var = ctk.StringVar(value=str(cfg.hash_max_mb))
        self._big_var = ctk.StringVar(value=str(cfg.big_file_mb))

        self._build_destination_row()

        ctk.CTkSwitch(
            self, text="Use USN journal (needs elevation -- see run-admin.bat)",
            variable=self._usn_var, font=theme.body_font(11),
        ).pack(anchor="w", padx=16, pady=8)

        self._build_number_row("Archive level (0-9)", self._level_var)
        self._build_number_row("Never-hash size ceiling (MB)", self._hash_var)
        self._build_number_row("Big-file checkbox threshold (MB)", self._big_var)

        self._roots_box = self._build_text_box("Extra roots (one path per line)", cfg.extra_roots)
        self._excludes_box = self._build_text_box("Extra excludes (one path per line)", cfg.extra_excludes)

        ctk.CTkButton(self, text="Save", command=self._save, fg_color=theme.SUCCESS).pack(side="bottom", pady=12)

    def _build_destination_row(self) -> None:
        ctk.CTkLabel(self, text="Destination", text_color=theme.TEXT, font=theme.body_font()).pack(
            anchor="w", padx=16, pady=(16, 2)
        )
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16)
        ctk.CTkEntry(row, textvariable=self._dest_var).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="Browse", width=80, command=self._browse).pack(side="right", padx=(8, 0))

    def _browse(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self._dest_var.set(path)

    def _build_number_row(self, label: str, var: ctk.StringVar) -> None:
        ctk.CTkLabel(self, text=label, text_color=theme.TEXT, font=theme.body_font(11)).pack(
            anchor="w", padx=16, pady=(6, 0)
        )
        ctk.CTkEntry(self, textvariable=var, width=100).pack(anchor="w", padx=16)

    def _build_text_box(self, label: str, values: list[str]) -> ctk.CTkTextbox:
        ctk.CTkLabel(self, text=label, text_color=theme.TEXT, font=theme.body_font(11)).pack(
            anchor="w", padx=16, pady=(6, 0)
        )
        box = ctk.CTkTextbox(self, height=60)
        box.insert("1.0", "\n".join(values))
        box.pack(fill="both", expand=True, padx=16)
        return box

    def _save(self) -> None:
        def _lines(box: ctk.CTkTextbox) -> list[str]:
            return [line.strip() for line in box.get("1.0", "end").splitlines() if line.strip()]

        cfg = config_mod.Config(
            destination_path=self._dest_var.get().strip(),
            extra_roots=_lines(self._roots_box),
            extra_excludes=_lines(self._excludes_box),
            use_usn=self._usn_var.get(),
            archive_level=int(self._level_var.get() or 5),
            hash_max_mb=int(self._hash_var.get() or 512),
            big_file_mb=int(self._big_var.get() or 100),
        )
        config_mod.save(cfg)
        self._on_saved(cfg)
        self.destroy()


def open_settings_dialog(master: ctk.CTk, cfg: config_mod.Config, on_saved: Callable[[config_mod.Config], None]) -> None:
    SettingsDialog(master, cfg, on_saved)
