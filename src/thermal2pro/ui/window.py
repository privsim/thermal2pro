#!/usr/bin/env python3
import os
import gi
import sys

# Use GTK 4.0
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
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
    def __init__(self, app, use_mock_camera=False):
        super().__init__(application=app)
        self.set_title("P2 Pro Thermal")
        
        # Set default window size
        self.set_default_size(800, 600)

        # Main vertical box
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.box.set_margin_top(5)
        self.box.set_margin_bottom(5)
        self.box.set_margin_start(5)
        self.box.set_margin_end(5)
        self.set_child(self.box)

        # Camera view area
        self.drawing_area = Gtk.DrawingArea()
        # Set minimum size to ensure proper rendering
        self.drawing_area.set_size_request(256, 192)
        # Set expand to fill available space
        self.drawing_area.set_vexpand(True)
        self.drawing_area.set_hexpand(True)
        
        self.drawing_area.set_draw_func(self.draw_frame)
        
        # Add drawing area to box
        self.box.append(self.drawing_area)

        # Mode selector bar
        mode_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        mode_bar.set_margin_bottom(5)
        mode_bar.set_margin_start(5)
        mode_bar.set_margin_end(5)

        # Create mode buttons
        self.mode_buttons = {}
        for mode in AppMode:
            button = Gtk.ToggleButton(label=mode.name.replace('_', ' '))
            button.set_can_focus(True)  # Enable keyboard focus
            button.set_focus_on_click(True)  # Focus when clicked
            button.connect('toggled', self.on_mode_button_toggled, mode)
            # Make buttons larger and more touch-friendly
            button.set_size_request(100, 40)
            mode_bar.append(button)
            self.mode_buttons[mode] = button

        # Add mode bar to main box
        self.box.append(mode_bar)

        # Controls container
        self.controls_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.controls_container.set_margin_top(5)
        self.controls_container.set_margin_bottom(5)
        self.controls_container.set_margin_start(5)
        self.controls_container.set_margin_end(5)

        # Add controls container to main box
        self.box.append(self.controls_container)

        # Initialize camera
        self.cap = None
        try:
            if use_mock_camera:
                logger.info("Using mock camera")
                self.cap = MockThermalCamera()
            else:
                logger.info("Attempting to initialize real camera")
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    raise RuntimeError("Failed to open camera")
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 192)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            if not self.cap or not self.cap.isOpened():
                logger.warning("Real camera not available, falling back to mock camera")
                self.cap = MockThermalCamera()
            
            logger.info("Camera initialized successfully")
            
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

        # Enable touch events
        self.set_receives_default(True)

        # Start in live view mode
        self.switch_mode(AppMode.LIVE_VIEW)

        # Show all widgets
        self.show()

        # Center window after showing
        display = self.get_display()
        if display:
            # Get primary monitor
            monitors = display.get_monitors()
            if monitors:
                monitor = monitors[0]  # Use primary monitor
                rect = monitor.get_geometry()
                x = (rect.width - 800) // 2
                y = (rect.height - 600) // 2
                self.set_default_size(800, 600)
                self.move(x, y)

        # Update frame every 16ms (targeting 60 FPS max)
        GLib.timeout_add(16, self.update_frame)
        logger.info("Window initialization complete")

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

    def on_mode_button_toggled(self, button, mode):
        """Handle mode button toggle."""
        if button.get_active():
            self.switch_mode(mode)
        elif mode == self.current_mode:
            # Don't allow deactivating current mode button
            button.set_active(True)

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
                    self.drawing_area.queue_draw()
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

    def do_close_request(self):
        """Clean up resources when window is closed."""
        # Clean up modes
        for mode in self.modes.values():
            mode.cleanup()

        # Release camera
        if self.cap is not None:
            self.cap.release()

        logger.info("Window resources cleaned up")
        return False
