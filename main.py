import queue
import tkinter as tk
import weakref
from datetime import datetime
from tkinter import ttk

import pyproxy_native
from ui.blocklist_panel import BlocklistPanel
from ui.header import Header
from ui.logs_panel import LogsPanel
from ui.proxy_controls import ProxyControls
from ui.statistics import StatisticsPanel
from ui.theme import BACKGROUND, ERROR, configure_styles, set_status_badge


class PyProxyApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.proxy: pyproxy_native.Proxy | None = None
        self._proxy_port = 8080
        self._domains: list[str] = []
        self._running = False
        self._closing = False
        self._proxy_events: queue.Queue[tuple[str, int]] = queue.Queue()
        self._stats = {
            "total_requests": 0,
            "forwarded_requests": 0,
            "blocked_requests": 0,
            "errors": 0,
            "active_connections": 0,
        }

        self.root.title("PyProxy — HTTP Proxy Control Panel")
        self.root.geometry("1120x820")
        self.root.minsize(900, 680)
        self.root.configure(bg=BACKGROUND)
        configure_styles(self.root)
        self._build()
        self.root.bind("<<ProxyEvent>>", self._handle_proxy_events)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.statistics.update_stats(self._stats)
        self.logs_panel.update_logs([])
        self._set_status("Stopped")
        self._update_controls()

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=(24, 20, 24, 18))
        outer.pack(fill="both", expand=True)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(4, weight=1)

        self.header = Header(outer)
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 18))

        self.proxy_controls = ProxyControls(
            outer,
            on_start=self._start,
            on_stop=self._stop,
            on_restart=self._restart,
        )
        self.proxy_controls.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        self.statistics = StatisticsPanel(outer)
        self.statistics.grid(row=2, column=0, sticky="ew", pady=(0, 16))

        content = ttk.Frame(outer)
        content.grid(row=4, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=3, uniform="content")
        content.grid_columnconfigure(1, weight=2, uniform="content")
        content.grid_rowconfigure(0, weight=1)

        self.logs_panel = LogsPanel(content)
        self.logs_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.blocklist_panel = BlocklistPanel(
            content,
            on_add=self._add_domain,
            on_remove=self._remove_domain,
        )
        self.blocklist_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.message_label = ttk.Label(
            outer,
            text="",
            foreground=ERROR,
            wraplength=1050,
            justify="left",
        )
        self.message_label.grid(row=5, column=0, sticky="ew", pady=(12, 0))

    def _set_status(self, status: str) -> None:
        set_status_badge(self.header.status_badge, status)

    def _show_error(self, message: str) -> None:
        self.message_label.configure(text=message, foreground=ERROR)

    def _clear_error(self) -> None:
        self.message_label.configure(text="")

    def _update_controls(self) -> None:
        self.proxy_controls.set_state(running=self._running)
        self.blocklist_panel.set_enabled(self._running)

    def _new_proxy(self, port: int) -> pyproxy_native.Proxy:
        proxy = pyproxy_native.Proxy(port)
        app_reference = weakref.ref(self)

        def on_proxy_event(name: str, value: int) -> None:
            app = app_reference()
            if app is not None:
                app._on_proxy_event(name, value)

        proxy.set_event_callback(on_proxy_event)
        for domain in self._domains:
            proxy.add_restricted_sites(domain)
        self._proxy_port = port
        return proxy

    def _on_proxy_event(self, name: str, value: int) -> None:
        if self._closing:
            return
        self._proxy_events.put((name, value))
        try:
            self.root.event_generate("<<ProxyEvent>>", when="tail")
        except tk.TclError:
            if not self._closing:
                raise

    def _handle_proxy_events(self, _event: tk.Event) -> None:
        while True:
            try:
                name, value = self._proxy_events.get_nowait()
            except queue.Empty:
                break

            if name in (
                "total_requests",
                "forwarded_requests",
                "blocked_requests",
                "errors",
            ):
                self._stats[name] += value
            elif name == "clientinc":
                self._stats["active_connections"] += value
            elif name == "clientdec":
                self._stats["active_connections"] = max(
                    0, self._stats["active_connections"] - value
                )
            else:
                continue

            self.statistics.update_stats(self._stats)
            log_details = {
                "clientinc": ("INFO", "Client connected"),
                "clientdec": ("INFO", "Client disconnected"),
                "forwarded_requests": ("INFO", "Request forwarded"),
                "blocked_requests": ("WARNING", "Request blocked"),
                "errors": ("ERROR", "Proxy request error"),
            }
            if name in log_details:
                severity, message = log_details[name]
                self.logs_panel.add_event(severity, message)

    def _start(self) -> None:
        try:
            port = self.proxy_controls.port()
            if self.proxy is None or port != self._proxy_port:
                self.proxy = self._new_proxy(port)
            self.proxy.start()
            self._running = True
            self._domains = self.proxy.get_restricted_sites()
            self.blocklist_panel.update_domains(self._domains)
            self._clear_error()
            self._set_status("Running")
        except (ValueError, RuntimeError) as error:
            self._show_error(str(error))
            self._set_status("Error")
        self._update_controls()

    def _stop(self) -> None:
        if self.proxy is None:
            return
        try:
            self.proxy.stop()
            self._running = False
            self._domains = self.proxy.get_restricted_sites()
            self.blocklist_panel.update_domains(self._domains)
            self._clear_error()
            self._set_status("Stopped")
        except RuntimeError as error:
            self._show_error(str(error))
            self._set_status("Error")
        self._update_controls()

    def _restart(self) -> None:
        try:
            port = self.proxy_controls.port()
            if self.proxy is None or port != self._proxy_port:
                self.proxy = self._new_proxy(port)
                self.proxy.start()
            else:
                self.proxy.restart()
            self._running = True
            self._domains = self.proxy.get_restricted_sites()
            self.blocklist_panel.update_domains(self._domains)
            self._clear_error()
            self._set_status("Running")
        except (ValueError, RuntimeError) as error:
            self._running = False
            self._show_error(str(error))
            self._set_status("Error")
        self._update_controls()

    def _add_domain(self, domain: str) -> None:
        domain = domain.strip()
        if not domain:
            self._show_error("Enter a domain before adding it.")
            return
        if self.proxy is None:
            self._show_error("Start the proxy before editing its blocklist.")
            return
        try:
            if not self.proxy.add_restricted_sites(domain):
                self._show_error(f"{domain} is already blocked.")
                return
            self._domains = self.proxy.get_restricted_sites()
            print(self._domains)
            self.blocklist_panel.update_domains(self._domains)
            self._clear_error()
        except RuntimeError as error:
            self._show_error(str(error))

    def _remove_domain(self, domain: str) -> None:
        if self.proxy is None:
            self._show_error("Start the proxy before editing its blocklist.")
            return
        try:
            if not self.proxy.remove_restricted_sites(domain):
                self._show_error(f"{domain} is not in the blocklist.")
                return
            self._domains = self.proxy.get_restricted_sites()
            self.blocklist_panel.update_domains(self._domains)
            self._clear_error()
        except RuntimeError as error:
            self._show_error(str(error))

    def _on_close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._set_status("Closing")
        if self.proxy is not None:
            try:
                if self._running:
                    self.proxy.stop()
            except RuntimeError as error:
                self._show_error(str(error))
            try:
                self.proxy.set_event_callback(None)
            except RuntimeError as error:
                self._show_error(str(error))
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    PyProxyApp(root)
    root.mainloop()
