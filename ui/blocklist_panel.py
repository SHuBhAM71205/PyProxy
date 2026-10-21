import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from ui.theme import PANEL_ALT, TEXT


class BlocklistPanel(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        on_add: Callable[[str], None],
        on_remove: Callable[[str], None],
    ) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(14, 12))
        self._domains: list[str] = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ttk.Label(self, text="Domain blocklist", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )

        add_row = ttk.Frame(self, style="Card.TFrame")
        add_row.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        add_row.grid_columnconfigure(0, weight=1)
        self.domain_entry = ttk.Entry(add_row)
        self.domain_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.domain_entry.bind("<Return>", lambda _event: self._add(on_add))
        self.add_button = ttk.Button(
            add_row,
            text="Add",
            style="Primary.TButton",
            command=lambda: self._add(on_add),
        )
        self.add_button.grid(row=0, column=1)

        list_area = ttk.Frame(self, style="Card.TFrame")
        list_area.grid(row=2, column=0, sticky="nsew")
        list_area.grid_columnconfigure(0, weight=1)
        list_area.grid_rowconfigure(0, weight=1)
        self.domain_list = tk.Listbox(
            list_area,
            exportselection=False,
            relief="flat",
            borderwidth=0,
            bg=PANEL_ALT,
            fg=TEXT,
            selectbackground="#164B70",
            selectforeground=TEXT,
            font=("Segoe UI", 10),
            activestyle="none",
        )
        self.domain_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            list_area, orient="vertical", command=self.domain_list.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.domain_list.configure(yscrollcommand=scrollbar.set)
        self.domain_list.bind("<<ListboxSelect>>", lambda _event: self._update_remove_state())

        self.remove_button = ttk.Button(
            self,
            text="Remove selected",
            command=lambda: self._remove(on_remove),
        )
        self.remove_button.grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.set_enabled(False)

    def update_domains(self, domains: list[str]) -> None:
        self._domains = list(domains)
        self.domain_list.delete(0, "end")
        if domains:
            for domain in domains:
                self.domain_list.insert("end", domain)
        else:
            self.domain_list.insert("end", "No blocked domains")
        self._update_remove_state()

    def set_enabled(self, enabled: bool) -> None:
        self.add_button.configure(state="normal" if enabled else "disabled")
        self.domain_entry.configure(state="normal" if enabled else "disabled")
        self._update_remove_state(enabled=enabled)

    def _add(self, callback: Callable[[str], None]) -> None:
        domain = self.domain_entry.get()
        callback(domain)

    def _remove(self, callback: Callable[[str], None]) -> None:
        selection = self.domain_list.curselection()
        if not selection or not self._domains:
            return
        domain = self.domain_list.get(selection[0])
        if domain in self._domains:
            callback(domain)

    def _update_remove_state(self, enabled: bool | None = None) -> None:
        if enabled is None:
            enabled = str(self.add_button.cget("state")) != "disabled"
        selection = self.domain_list.curselection()
        can_remove = enabled and bool(selection) and bool(self._domains)
        self.remove_button.configure(state="normal" if can_remove else "disabled")
