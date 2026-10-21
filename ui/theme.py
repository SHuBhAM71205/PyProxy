import tkinter as tk
from tkinter import ttk


BLUE = "#1268B3"
GOLD = "#F2B51B"
BACKGROUND = "#151B23"
PANEL = "#202A35"
PANEL_ALT = "#263341"
TEXT = "#E7EDF3"
TEXT_MUTED = "#A5B2BF"
BORDER = "#354454"
WHITE = "#FFFFFF"
MUTED = TEXT_MUTED
ERROR = "#FF7B72"
SUCCESS = "#57D18C"


def configure_styles(root: tk.Tk) -> None:
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure("TFrame", background=BACKGROUND)
    style.configure(
        "Card.TFrame",
        background=PANEL,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "TLabel",
        background=BACKGROUND,
        foreground=TEXT,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Title.TLabel",
        font=("Segoe UI Semibold", 20),
        foreground=TEXT,
    )
    style.configure(
        "Subtitle.TLabel",
        font=("Segoe UI", 10),
        foreground=MUTED,
    )
    style.configure(
        "Section.TLabel",
        font=("Segoe UI Semibold", 11),
        foreground=TEXT,
    )
    style.configure(
        "CardTitle.TLabel",
        background=PANEL,
        font=("Segoe UI", 9),
        foreground=MUTED,
    )
    style.configure(
        "StatValue.TLabel",
        background=PANEL,
        font=("Segoe UI Semibold", 20),
        foreground=TEXT,
    )
    style.configure(
        "TButton",
        background=PANEL_ALT,
        foreground=TEXT,
        font=("Segoe UI Semibold", 9),
        padding=(12, 7),
    )
    style.map(
        "TButton",
        background=[
            ("active", "#344456"),
            ("disabled", PANEL),
        ],
        foreground=[("disabled", "#697887")],
    )
    style.configure(
        "Primary.TButton",
        background=BLUE,
        foreground=WHITE,
    )
    style.map(
        "Primary.TButton",
        background=[("active", "#197AC8"), ("disabled", "#344456")],
        foreground=[("disabled", "#93A1AE")],
    )
    style.configure(
        "Stop.TButton",
        background="#422B30",
        foreground=ERROR,
    )
    style.map(
        "Stop.TButton",
        background=[("active", "#563239"), ("disabled", PANEL)],
        foreground=[("disabled", "#78686B")],
    )
    style.configure(
        "TEntry",
        padding=(8, 7),
        fieldbackground=PANEL_ALT,
        foreground=TEXT,
        insertcolor=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
    )
    style.configure(
        "TCheckbutton",
        background=PANEL,
        foreground=MUTED,
    )
    style.map(
        "TCheckbutton",
        background=[("active", PANEL)],
        foreground=[("disabled", "#697887")],
    )
    style.configure(
        "TScrollbar",
        arrowsize=12,
        background=PANEL_ALT,
        troughcolor=BACKGROUND,
        bordercolor=BACKGROUND,
        arrowcolor=MUTED,
    )


def create_status_badge(parent: tk.Misc) -> tk.Label:
    return tk.Label(
        parent,
        text="Checking",
        bg="#263341",
        fg=TEXT,
        font=("Segoe UI Semibold", 9),
        padx=11,
        pady=6,
    )


def set_status_badge(badge: tk.Label, status: str) -> None:
    colors = {
        "Running": ("#203A31", SUCCESS),
        "Stopped": ("#263341", TEXT_MUTED),
        "Error": ("#432B31", ERROR),
        "Checking": ("#1C3448", "#64B5F6"),
        "Closing": ("#263341", TEXT_MUTED),
    }
    background, foreground = colors.get(status, ("#263341", TEXT_MUTED))
    badge.configure(text=status, bg=background, fg=foreground)
