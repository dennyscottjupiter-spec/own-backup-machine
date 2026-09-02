# ---
# purpose: dark palette + fonts shared by every panel — the only place colors are literals
# exports: apply(), heading_font(), body_font(), color constants
# ---
from __future__ import annotations

import customtkinter as ctk

BG = "#1a1a1a"
PANEL_BG = "#242424"
ACCENT = "#3b82f6"
TEXT = "#e5e5e5"
MUTED = "#9ca3af"
DANGER = "#ef4444"
WARNING = "#f59e0b"
SUCCESS = "#22c55e"

FONT_FAMILY = "Segoe UI"


def apply() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def heading_font(size: int = 16) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")


def body_font(size: int = 12) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size)
