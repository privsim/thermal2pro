#!/usr/bin/env python3
import gi
import signal
import sys
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    gi.require_version('Gtk', '4.0')
    logger.info("Using GTK 4.0")
except ValueError:
    gi.require_version('Gtk', '3.0')
    logger.info("Falling back to GTK 3.0")

from gi.repository import Gtk, GLib

from thermal2pro.ui.window import ThermalWindow

class ThermalApp(Gtk.Application):
    def __init__(self, use_mock_camera=False):
        super().__init__()
        self._window = None
        self.use_mock_camera = use_mock_camera
        self.setup_signal_handlers()
        logger.info("ThermalApp initialized")

    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        try:
            # Use GLib's unix signal handling
            GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self.on_sigint)
            GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.on_sigterm)
            logger.info("Signal handlers set up successfully")
        except Exception as e:
            logger.error(f"Failed to set up signal handlers: {e}")

    def on_sigint(self):
        """Handle SIGINT (Ctrl+C) gracefully."""
        logger.info("Received SIGINT. Shutting down gracefully...")
        self.quit()
        return GLib.SOURCE_REMOVE

    def on_sigterm(self):
        """Handle SIGTERM gracefully."""
        logger.info("Received SIGTERM. Shutting down gracefully...")
        self.quit()
        return GLib.SOURCE_REMOVE

    def do_startup(self):
        """Called when application is starting up."""
        try:
            Gtk.Application.do_startup(self)
            logger.info("Application startup completed")
        except Exception as e:
            logger.error(f"Error during startup: {e}")
            sys.exit(1)

    def do_activate(self):
        """Called when application is activated."""
        try:
            if not self._window:
                self._window = ThermalWindow(self, use_mock_camera=self.use_mock_camera)
                logger.info("Main window created")
            self._window.present()
            logger.info("Window presented")
        except Exception as e:
            logger.error(f"Error activating window: {e}")
            self.quit()

    def do_shutdown(self):
        """Called when application is shutting down."""
        try:
            if self._window:
                self._window.destroy()
            Gtk.Application.do_shutdown(self)
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

@contextmanager
def handle_keyboard_interrupt():
    """Context manager to handle KeyboardInterrupt gracefully."""
    try:
        yield
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt. Shutting down gracefully...")
        sys.exit(0)

def main():
    try:
        # Check if we should use mock camera
        use_mock = "--mock" in sys.argv
        if use_mock:
            logger.info("Starting in mock camera mode")
        
        app = ThermalApp(use_mock_camera=use_mock)
        with handle_keyboard_interrupt():
            return app.run(None)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
