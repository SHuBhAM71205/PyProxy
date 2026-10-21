import tkinter as tk
from tkinter import ttk


STAT_TITLES = (
    ("total_requests", "Total requests"),
    ("forwarded_requests", "Forwarded"),
    ("blocked_requests", "Blocked"),
    ("errors", "Request errors"),
    ("active_connections", "Active connections"),
)


class StatisticsPanel(ttk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.values: dict[str, ttk.Label] = {}
        for column, (key, title) in enumerate(STAT_TITLES):
            self.grid_columnconfigure(column, weight=1, uniform="stats")
            card = ttk.Frame(self, style="Card.TFrame", padding=(13, 11))
            card.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 5, 5 if column < 4 else 0),
            )
            ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="—", style="StatValue.TLabel")
            value.pack(anchor="w", pady=(5, 0))
            self.values[key] = value

    def update_stats(self, stats: dict[str, int | None] | None) -> None:
        for key, _title in STAT_TITLES:
            value = None if stats is None else stats.get(key)
            text = "Unavailable" if stats is None else "—" if value is None else f"{value:,}"
            self.values[key].configure(text=text)
