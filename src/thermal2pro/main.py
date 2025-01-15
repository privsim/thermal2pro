#!/usr/bin/env python3
import gi
import signal
import sys
from contextlib import contextmanager

try:
    gi.require_version('Gtk', '4.0')
except ValueError:
    gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from thermal2pro.ui.window import ThermalWindow

class ThermalApp(Gtk.Application):
    def __init__(self):
        super().__init__()
        self._window = None
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        # Use GLib's unix signal handling
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self.on_sigint)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.on_sigterm)

    def on_sigint(self):
        """Handle SIGINT (Ctrl+C) gracefully."""
        print("\nReceived SIGINT. Shutting down gracefully...")
        self.quit()
        return GLib.SOURCE_REMOVE

    def on_sigterm(self):
        """Handle SIGTERM gracefully."""
        print("\nReceived SIGTERM. Shutting down gracefully...")
        self.quit()
        return GLib.SOURCE_REMOVE

    def do_startup(self):
        """Called when application is starting up."""
        Gtk.Application.do_startup(self)

    def do_activate(self):
        """Called when application is activated."""
        if not self._window:
            self._window = ThermalWindow(self)
        self._window.present()

    def do_shutdown(self):
        """Called when application is shutting down."""
        if self._window:
            self._window.destroy()
        Gtk.Application.do_shutdown(self)

@contextmanager
def handle_keyboard_interrupt():
    """Context manager to handle KeyboardInterrupt gracefully."""
    try:
        yield
    except KeyboardInterrupt:
        print("\nReceived KeyboardInterrupt. Shutting down gracefully...")
        sys.exit(0)

def main():
    app = ThermalApp()
    with handle_keyboard_interrupt():
        return app.run(None)

if __name__ == "__main__":
    main()
