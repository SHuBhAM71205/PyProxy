import tkinter as tk
from datetime import datetime
from tkinter import ttk

from ui.theme import BLUE, PANEL_ALT, TEXT, ERROR


class LogsPanel(ttk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(14, 12))
        self._current_logs: list[dict[str, str]] = []
        self._last_logs: list[dict[str, str]] = []
        self._auto_scroll = tk.BooleanVar(value=True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="Card.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)
        ttk.Label(header, text="Live logs", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Checkbutton(
            header, text="Auto-scroll", variable=self._auto_scroll
        ).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(
            header, text="Clear visible", command=self.clear_visible
        ).grid(row=0, column=2)

        log_area = ttk.Frame(self, style="Card.TFrame")
        log_area.grid(row=1, column=0, sticky="nsew")
        log_area.grid_columnconfigure(0, weight=1)
        log_area.grid_rowconfigure(0, weight=1)
        self.text = tk.Text(
            log_area,
            wrap="word",
            state="disabled",
            bg=PANEL_ALT,
            fg=TEXT,
            relief="flat",
            padx=10,
            pady=8,
            font=("Consolas", 9),
            selectbackground="#164B70",
            insertbackground=TEXT,
        )
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_area, orient="vertical", command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.tag_configure("INFO", foreground=BLUE)
        self.text.tag_configure("WARNING", foreground="#F2B84B")
        self.text.tag_configure("ERROR", foreground=ERROR)
        self.text.tag_configure("message", foreground=TEXT)

    def update_logs(self, logs: list[dict[str, str]] | None) -> None:
        if logs is None:
            self._current_logs = []
            self._last_logs = []
            self._replace_text("Backend log retrieval is not supported.")
            return
        if not logs:
            self._current_logs = []
            self._last_logs = []
            self._replace_text("No logs available yet.")
            return

        common_prefix = 0
        while (
            common_prefix < len(self._last_logs)
            and common_prefix < len(logs)
            and self._last_logs[common_prefix] == logs[common_prefix]
        ):
            common_prefix += 1
        if not self._last_logs or common_prefix < len(self._last_logs):
            self._replace_text("")
            start_at = 0
        else:
            start_at = common_prefix
        for entry in logs[start_at:]:
            self._append(entry)
        self._last_logs = list(logs)
        self._current_logs = list(logs)

    def clear_visible(self) -> None:
        self._replace_text("")
        self._last_logs = list(self._current_logs)

    def add_event(self, severity: str, message: str) -> None:
        if not self._current_logs:
            self._replace_text("")
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "severity": severity,
            "message": message,
        }
        self._current_logs.append(entry)
        self._last_logs.append(entry)
        self._append(entry)

    def _append(self, entry: dict[str, str]) -> None:
        self.text.configure(state="normal")
        timestamp = f"[{entry['timestamp']}] " if entry["timestamp"] else ""
        self.text.insert("end", timestamp)
        self.text.insert("end", f"{entry['severity']:<7} ", entry["severity"])
        self.text.insert("end", entry["message"] + "\n", "message")
        self.text.configure(state="disabled")
        if self._auto_scroll.get():
            self.text.see("end")

    def _replace_text(self, value: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        if value:
            self.text.insert("end", value)
        self.text.configure(state="disabled")
