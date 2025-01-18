#!/usr/bin/env python3
import os
import gi
import sys
import logging
import argparse
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set GTK version based on environment or default to 4.0
GTK_VERSION = os.environ.get('GTK_VERSION', '4.0')
try:
    gi.require_version('Gtk', GTK_VERSION)
    logger.info(f"Using GTK {GTK_VERSION}")
except ValueError as e:
    logger.warning(f"Failed to use GTK {GTK_VERSION}, falling back to GTK 3.0")
    gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from thermal2pro.ui.window import ThermalWindow

def signal_handler(signum, frame):
    """Handle system signals gracefully."""
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    sys.exit(0)

class ThermalApp(Gtk.Application):
    def __init__(self, use_mock_camera=False):
        super().__init__()
        self.use_mock_camera = use_mock_camera
        logger.info("ThermalApp initialized")

    def do_startup(self):
        """Handle application startup."""
        Gtk.Application.do_startup(self)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("Signal handlers set up successfully")

    def do_activate(self):
        """Handle application activation."""
        try:
            win = ThermalWindow(self, use_mock_camera=self.use_mock_camera)
            win.present()
            logger.info("Window presented")
        except Exception as e:
            logger.error(f"Error activating window: {e}")
            self.quit()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Thermal2Pro Camera Application')
    parser.add_argument('--mock', action='store_true', help='Use mock camera for testing')
    args = parser.parse_args()

    if args.mock:
        logger.info("Starting in mock camera mode")

    try:
        app = ThermalApp(use_mock_camera=args.mock)
        logger.info("Application startup completed")
        exit_status = app.run(None)
        logger.info("Application shutdown completed")
        return exit_status
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
