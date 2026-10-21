import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


class ProxyControls(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
        on_restart: Callable[[], None],
    ) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(16, 14))
        self.grid_columnconfigure(1, weight=1)

        ttk.Label(self, text="Proxy controls", style="Section.TLabel").grid(
            row=0, column=0, columnspan=5, sticky="w", pady=(0, 11)
        )
        ttk.Label(self, text="Port").grid(row=1, column=0, sticky="w", padx=(0, 8))
        self.port_entry = ttk.Entry(self, width=8)
        self.port_entry.insert(0, "8080")
        self.port_entry.grid(row=1, column=1, sticky="w", padx=(0, 18))

        self.start_button = ttk.Button(
            self, text="Start", style="Primary.TButton", command=on_start
        )
        self.stop_button = ttk.Button(
            self, text="Stop", style="Stop.TButton", command=on_stop
        )
        self.restart_button = ttk.Button(self, text="Restart", command=on_restart)
        self.start_button.grid(row=1, column=2, padx=(0, 8))
        self.stop_button.grid(row=1, column=3, padx=(0, 8))
        self.restart_button.grid(row=1, column=4)

    def port(self) -> int:
        port = int(self.port_entry.get())
        if not 1 <= port <= 65535:
            raise ValueError("Port must be between 1 and 65535.")
        return port

    def set_state(self, *, running: bool) -> None:
        self.start_button.configure(
            state="disabled" if running else "normal"
        )
        self.stop_button.configure(
            state="normal" if running else "disabled"
        )
        self.restart_button.configure(
            state="normal" if running else "disabled"
        )
