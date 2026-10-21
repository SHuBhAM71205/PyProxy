import tkinter as tk
from tkinter import ttk

from ui.theme import BLUE, GOLD, WHITE, create_status_badge


class Header(ttk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.grid_columnconfigure(1, weight=1)

        mark = tk.Frame(self, width=48, height=48, bg=BLUE)
        mark.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 13))
        mark.grid_propagate(False)
        tk.Label(
            mark,
            text="P",
            bg=BLUE,
            fg=WHITE,
            font=("Segoe UI Semibold", 25),
        ).place(relx=0.5, rely=0.48, anchor="center")
        tk.Frame(mark, bg=GOLD, height=4, width=17).place(
            relx=1, rely=1, anchor="se"
        )

        ttk.Label(self, text="PyProxy", style="Title.TLabel").grid(
            row=0, column=1, sticky="sw"
        )
        ttk.Label(
            self, text="HTTP Proxy Control Panel", style="Subtitle.TLabel"
        ).grid(row=1, column=1, sticky="nw")

        self.status_badge = create_status_badge(self)
        self.status_badge.grid(row=0, column=2, rowspan=2, sticky="e")
