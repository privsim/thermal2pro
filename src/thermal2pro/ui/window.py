#!/usr/bin/env python3
import os
import gi
import sys
try:
    gi.require_version('Gtk', os.environ.get('GTK_VERSION', '3.0'))
except ValueError:
    gi.require_version('Gtk', '3.0')
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
        
        # Center window - handle GTK version differences
        if hasattr(Gtk.WindowPosition, 'CENTER'):
            # GTK3 style
            self.set_position(Gtk.WindowPosition.CENTER)
        else:
            # GTK4 style - default to center
            screen = self.get_screen()
            if screen:
                monitor = screen.get_monitor_at_window(screen.get_active_window())
                geometry = monitor.get_geometry()
                x = (geometry.width - 800) // 2
                y = (geometry.height - 600) // 2
                self.move(x, y)

        # Main vertical box
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        if Gtk._version.startswith('4'):
            self.set_child(self.box)
        else:
            self.add(self.box)

        # Camera view area
        self.drawing_area = Gtk.DrawingArea()
        if Gtk._version.startswith('4'):
            self.drawing_area.set_draw_func(self.draw_frame)
        else:
            self.drawing_area.connect("draw", self.draw_frame_gtk3)
        
        # Add drawing area to box
        if Gtk._version.startswith('4'):
            self.box.append(self.drawing_area)
        else:
            self.box.pack_start(self.drawing_area, True, True, 0)

        # Mode selector bar
        mode_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        mode_bar.set_spacing(5)
        if Gtk._version.startswith('4'):
            mode_bar.set_margin_start(5)
            mode_bar.set_margin_end(5)
            mode_bar.set_margin_top(5)
        else:
            mode_bar.set_margin_left(5)
            mode_bar.set_margin_right(5)
            mode_bar.set_margin_top(5)

        # Create mode buttons
        self.mode_buttons = {}
        for mode in AppMode:
            button = Gtk.ToggleButton(label=mode.name.replace('_', ' '))
            button.connect('toggled', self.on_mode_button_toggled, mode)
            if Gtk._version.startswith('4'):
                mode_bar.append(button)
            else:
                mode_bar.pack_start(button, True, True, 0)
            self.mode_buttons[mode] = button

        # Add mode bar to main box
        if Gtk._version.startswith('4'):
            self.box.append(mode_bar)
        else:
            self.box.pack_start(mode_bar, False, False, 0)

        # Controls container
        self.controls_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.controls_container.set_spacing(10)
        if Gtk._version.startswith('4'):
            self.controls_container.set_margin_start(10)
            self.controls_container.set_margin_end(10)
            self.controls_container.set_margin_bottom(10)
        else:
            self.controls_container.set_margin_left(10)
            self.controls_container.set_margin_right(10)
            self.controls_container.set_margin_bottom(10)

        # Add controls container to main box
        if Gtk._version.startswith('4'):
            self.box.append(self.controls_container)
        else:
            self.box.pack_start(self.controls_container, False, False, 0)

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

        # Initialize modes
        self.modes = {
            AppMode.LIVE_VIEW: LiveViewMode(self),
            # Other modes will be added as they're implemented
        }
        self.current_mode = None

        # Start in live view mode
        self.switch_mode(AppMode.LIVE_VIEW)

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
            return True
        except Exception as e:
            logger.error(f"Error updating frame: {e}")
            return False

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

    def draw_frame_gtk3(self, widget, ctx):
        """GTK3 draw callback."""
        return self.draw_frame(widget, ctx, widget.get_allocated_width(), 
                             widget.get_allocated_height())

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
