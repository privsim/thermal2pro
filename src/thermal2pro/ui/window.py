"""Main window implementation."""
import os
import gi
import sys
import platform

# Use GTK 4.0
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Gio
from importlib import resources
from pathlib import Path
import cv2
import numpy as np
from datetime import datetime
import cairo
from pathlib import Path
import logging
from thermal2pro.ui.cairo_handler import CairoSurfaceHandler
from thermal2pro.ui.live_view import LiveViewHandler
from thermal2pro.camera.mock_camera import MockThermalCamera
from thermal2pro.ui.modes import AppMode, LiveViewMode

logger = logging.getLogger(__name__)

class ThermalWindow(Gtk.ApplicationWindow):
    """Main application window."""
    
    def __init__(self, app, use_mock_camera=False):
        """Initialize window.
        
        Args:
            app: GTK application
        """
        super().__init__(application=app)
        self.set_title("P2 Pro Thermal")
        
        # Load CSS styling
        css_provider = Gtk.CssProvider()
        try:
            css_file = Path(resources.files('thermal2pro.ui') / 'style.css')
            css_provider.load_from_path(str(css_file))
        except Exception as e:
            logger.warning(f"Failed to load CSS: {e}")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Set window size before creating content
        self.set_default_size(800, 600)

        # Main vertical box
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.box.set_margin_top(5)
        self.box.set_margin_bottom(5)
        self.box.set_margin_start(5)
        self.box.set_margin_end(5)
        self.set_child(self.box)

        # Initialize modes first
        self.modes = {
            AppMode.LIVE_VIEW: LiveViewMode(self),
            # Other modes will be added as they're implemented
        }
        self.current_mode = None

        # Camera view area
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(256, 192)
        self.drawing_area.set_vexpand(True)
        self.drawing_area.set_hexpand(True)
        self.drawing_area.set_draw_func(self.draw_frame)
        self.box.append(self.drawing_area)

        # Mode selector bar
        mode_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        mode_bar.set_margin_bottom(5)
        mode_bar.set_margin_start(5)
        mode_bar.set_margin_end(5)

        # Create mode buttons
        self.mode_buttons = {}
        for mode in AppMode:
            button = Gtk.ToggleButton()
            button.set_label(mode.name.replace('_', ' '))
            button.set_can_focus(True)
            button.set_has_frame(True)  # Ensure button has visible frame
            button.set_size_request(120, 50)  # Larger touch targets
            button.connect('toggled', self.on_mode_button_toggled, mode)
            button.add_css_class('mode-button')
            if mode == AppMode.LIVE_VIEW:  # Set initial active state
                button.set_active(True)
            mode_bar.append(button)
            self.mode_buttons[mode] = button

        self.box.append(mode_bar)

        # Controls container
        self.controls_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.controls_container.set_margin_top(5)
        self.controls_container.set_margin_bottom(5)
        self.controls_container.set_margin_start(5)
        self.controls_container.set_margin_end(5)
        self.box.append(self.controls_container)

        # Initialize camera
        self.cap = None
        if use_mock_camera:
            logger.info("Using mock camera as requested")
            self.cap = MockThermalCamera()
        else:
            try:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    raise RuntimeError("Failed to open camera")
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 192)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                
            except Exception as e:
                logger.warning(f"Camera initialization failed: {e}, falling back to mock camera")
                self.cap = MockThermalCamera()

        # Initialize frame buffer
        self.current_frame = None

        # Initialize modes
        self.modes = {
            AppMode.LIVE_VIEW: LiveViewMode(self),
            # Other modes will be added as they're implemented
        }
        self.current_mode = None

        # Start in live view mode
        self.switch_mode(AppMode.LIVE_VIEW)

        # Show window - GTK4 uses set_visible instead of show/show_all
        self.set_visible(True)

        # Update frame every 16ms (targeting 60 FPS max)
        GLib.timeout_add(16, self.update_frame)
        logger.info("Window initialization complete")

    def _on_monitor_changed(self, display, monitor=None):
        """Handle monitor configuration changes."""
        if self.get_visible():
            self._update_window_position()

    def _update_window_position(self):
        """Update window position based on current monitor configuration."""
        try:
            display = self.get_display()
            if not display:
                return

            # Get monitors list
            monitors = display.get_monitors()
            if monitors.get_n_items() == 0:
                return

            # Get primary monitor
            monitor = monitors.get_item(0)
            geometry = monitor.get_geometry()

            # Calculate center position
            width = geometry.width
            height = geometry.height
            window_size = self.get_default_size()

            x = (width - window_size[0]) // 2 if width > window_size[0] else 0
            y = (height - window_size[1]) // 2 if height > window_size[1] else 0

            # Get window surface
            surface = self.get_surface()
            if surface:
                surface.set_position(x, y)
        except Exception as e:
            logger.warning(f"Error updating window position: {e}")

    def switch_mode(self, mode):
        """Switch to specified mode."""
        if self.current_mode == mode:
            return

        logger.info(f"Switching to {mode.name} mode")

        # Deactivate current mode
        if self.current_mode is not None:
            current = self.modes.get(self.current_mode)
            if current:
                current.deactivate()
                self.mode_buttons[self.current_mode].set_active(False)

        # Activate new mode
        self.current_mode = mode
        new_mode = self.modes.get(mode)
        if new_mode:
            new_mode.activate()
            self.mode_buttons[mode].set_active(True)
            
        # Force a redraw
        self.queue_draw()
        if self.controls_container:
            self.controls_container.queue_draw()

    def on_mode_button_toggled(self, button, mode):
        """Handle mode button toggle."""
        logger.debug(f"Mode button toggled: {mode.name}, active: {button.get_active()}")
        if button.get_active():
            self.switch_mode(mode)
        elif mode == self.current_mode:
            # Don't allow deactivating current mode button
            button.set_active(True)
            
        # Update other buttons
        for m, btn in self.mode_buttons.items():
            if m != mode:
                btn.set_active(False)

    def update_frame(self):
        """Update current frame."""
        try:
            ret, frame = self.cap.read()
            if ret:
                # Get current mode
                mode = self.modes.get(self.current_mode)
                if mode:
                    # Process frame through current mode
                    self.current_frame = mode.process_frame(frame)
                    self.queue_draw()  # GTK4 uses queue_draw instead of queue_draw_area
            return True  # Continue updates
        except Exception as e:
            logger.error(f"Error updating frame: {e}")
            return True  # Continue updates even on error

    def draw_frame(self, area, ctx, width, height):
        """Draw current frame."""
        if self.current_frame is None:
            return

        try:
            surface = CairoSurfaceHandler.create_surface_from_frame(self.current_frame)
            CairoSurfaceHandler.scale_and_center(ctx, surface, width, height)
            
            # Draw mode overlay
            mode = self.modes.get(self.current_mode)
            if mode:
                mode.draw_overlay(ctx, width, height)
        except Exception as e:
            logger.error(f"Error drawing frame: {e}")
            return False

    def close(self):
        """Close window and clean up resources."""
        logger.info("Starting window cleanup...")
        
        try:
            # Stop frame updates
            GLib.source_remove_by_user_data(self.update_frame)
        except Exception as e:
            logger.warning(f"Error removing frame update source: {e}")
        
        # Clean up modes
        for mode in self.modes.values():
            try:
                mode.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up mode {mode}: {e}")

        # Release camera
        if self.cap is not None:
            try:
                self.cap.release()
                self.cap = None
            except Exception as e:
                logger.warning(f"Error releasing camera: {e}")

        # Clear frame buffer
        self.current_frame = None

        # Run garbage collection
        import gc
        gc.collect()

        logger.info("Window resources cleaned up")
        super().close()