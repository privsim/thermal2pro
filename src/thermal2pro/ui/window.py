#!/usr/bin/env python3
import gi
import sys
try:
    gi.require_version('Gtk', '4.0')
except ValueError:
    gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import cv2
import numpy as np
from datetime import datetime
import cairo
from pathlib import Path
from thermal2pro.ui.cairo_handler import CairoSurfaceHandler
from thermal2pro.ui.live_view import LiveViewHandler

class ThermalWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("P2 Pro Thermal")
        self.fullscreen()

        # Main vertical box
        if Gtk._version == "4.0":
            self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.set_child(self.box)
        else:
            self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.add(self.box)

        # Camera view area
        self.drawing_area = Gtk.DrawingArea()
        if Gtk._version == "4.0":
            self.drawing_area.set_draw_func(self.draw_frame)
        else:
            self.drawing_area.connect("draw", self.draw_frame_gtk3)
        self.box.append(self.drawing_area)

        # Button bar at bottom
        button_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_bar.set_spacing(10)
        if Gtk._version == "4.0":
            button_bar.set_margin_start(10)
            button_bar.set_margin_end(10)
            button_bar.set_margin_bottom(10)
        else:
            button_bar.set_margin_left(10)
            button_bar.set_margin_right(10)
            button_bar.set_margin_bottom(10)

        # Large touch-friendly capture button
        capture_button = Gtk.Button(label="Capture")
        capture_button.connect("clicked", self.capture_image)
        capture_button.set_vexpand(False)
        capture_button.set_hexpand(True)
        if Gtk._version == "4.0":
            button_bar.append(capture_button)
        else:
            button_bar.pack_start(capture_button, True, True, 0)

        # Color palette selector
        if Gtk._version == "4.0":
            palette_store = Gtk.StringList()
            for name in ["Iron", "Rainbow", "Gray"]:
                palette_store.append(name)
            self.palette_dropdown = Gtk.DropDown(model=palette_store)
        else:
            palette_store = Gtk.ListStore(str)
            for name in ["Iron", "Rainbow", "Gray"]:
                palette_store.append([name])
            self.palette_dropdown = Gtk.ComboBox.new_with_model(palette_store)
            renderer_text = Gtk.CellRendererText()
            self.palette_dropdown.pack_start(renderer_text, True)
            self.palette_dropdown.add_attribute(renderer_text, "text", 0)

        self.palette_dropdown.connect("changed" if Gtk._version == "3.0" else "notify::selected", self.change_palette)
        self.palette_dropdown.set_vexpand(False)
        self.palette_dropdown.set_hexpand(True)
        if Gtk._version == "4.0":
            button_bar.append(self.palette_dropdown)
        else:
            button_bar.pack_start(self.palette_dropdown, True, True, 0)

        # Performance metrics toggle button
        metrics_button = Gtk.Button(label="Metrics")
        metrics_button.connect("clicked", self.toggle_metrics)
        metrics_button.set_vexpand(False)
        metrics_button.set_hexpand(False)
        if Gtk._version == "4.0":
            button_bar.append(metrics_button)
        else:
            button_bar.pack_start(metrics_button, False, False, 0)

        if Gtk._version == "4.0":
            self.box.append(button_bar)
        else:
            self.box.pack_start(button_bar, False, False, 0)

        # Initialize camera
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Failed to open camera")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 192)
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering
            self.cap.set(cv2.CAP_PROP_FPS, 30)  # Target 30 FPS
        except Exception as e:
            print(f"Error initializing camera: {e}")
            print("Check if the camera is connected and you have permission to access it")
            print("You might need: sudo usermod -a -G video $USER")
            sys.exit(1)

        self.current_palette = cv2.COLORMAP_JET
        self.current_frame = None
        self.live_view = LiveViewHandler(buffer_size=5)  # 5 frame buffer
        self.show_metrics = False

        # Update frame every 16ms (targeting 60 FPS max)
        GLib.timeout_add(16, self.update_frame)

    def update_frame(self):
        try:
            ret, frame = self.cap.read()
            if ret:
                # Convert to grayscale and apply color palette
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                colored = cv2.applyColorMap(gray, self.current_palette)
                rgb_frame = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
                
                # Process frame through live view handler
                processed_frame, _ = self.live_view.process_frame(rgb_frame)
                if processed_frame is not None:
                    self.current_frame = processed_frame
                    self.drawing_area.queue_draw()
            return True
        except Exception as e:
            print(f"Error updating frame: {e}")
            return False

    def draw_frame(self, area, ctx, width, height):
        if self.current_frame is None:
            return

        try:
            surface = CairoSurfaceHandler.create_surface_from_frame(self.current_frame)
            CairoSurfaceHandler.scale_and_center(ctx, surface, width, height)
            
            if self.show_metrics:
                self.draw_metrics_overlay(ctx, width, height)
        except Exception as e:
            print(f"Error drawing frame: {e}")
            return False

    def draw_frame_gtk3(self, widget, ctx):
        return self.draw_frame(widget, ctx, widget.get_allocated_width(), 
                             widget.get_allocated_height())

    def draw_metrics_overlay(self, ctx, width, height):
        """Draw performance metrics overlay."""
        metrics = self.live_view.get_metrics()
        
        # Setup overlay style
        ctx.save()
        ctx.set_source_rgba(0, 0, 0, 0.7)  # Semi-transparent black background
        ctx.rectangle(10, 10, 200, 90)
        ctx.fill()
        
        ctx.set_source_rgb(1, 1, 1)  # White text
        ctx.select_font_face("monospace")
        ctx.set_font_size(14)
        
        # Draw metrics
        y = 30
        for label, value in [
            ("FPS", f"{metrics.fps:.1f}"),
            ("Frame Time", f"{metrics.frame_time*1000:.1f}ms"),
            ("Dropped Frames", str(metrics.dropped_frames)),
            ("Buffer Usage", f"{metrics.buffer_usage*100:.0f}%")
        ]:
            ctx.move_to(20, y)
            ctx.show_text(f"{label}: {value}")
            y += 20
            
        ctx.restore()

    def capture_image(self, button):
        if self.current_frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            capture_dir = Path("/mnt/thermal_storage/thermal_captures")
            if not capture_dir.exists():
                capture_dir = Path.home() / "thermal_captures"
                capture_dir.mkdir(exist_ok=True)
            
            filepath = capture_dir / f"thermal_{timestamp}.jpg"
            try:
                cv2.imwrite(str(filepath),
                           cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR))
                print(f"Captured: {filepath}")
            except Exception as e:
                print(f"Error saving capture: {e}")

    def change_palette(self, dropdown, *args):
        palette_map = {
            0: cv2.COLORMAP_HOT,    # Iron
            1: cv2.COLORMAP_JET,    # Rainbow
            2: cv2.COLORMAP_BONE    # Gray
        }
        if Gtk._version == "4.0":
            selected = dropdown.get_selected()
        else:
            selected = dropdown.get_active()
        self.current_palette = palette_map[selected]

    def toggle_metrics(self, button):
        """Toggle performance metrics overlay."""
        self.show_metrics = not self.show_metrics
        self.drawing_area.queue_draw()

    def do_close_request(self):
        """Clean up resources when window is closed."""
        if self.cap is not None:
            self.cap.release()
        self.live_view.clear_buffer()
        return False
