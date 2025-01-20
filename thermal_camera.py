#!/usr/bin/env python3
import sys
import gi

# Use GTK 4.0 exclusively
gi.require_version('Gtk', '4.0')
try:
    from gi.repository import Gtk, GLib, Gdk
except ImportError as e:
    print("Error: PyGObject with GTK4 not found. Install system dependencies with:")
    print("sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 libgirepository1.0-dev")
    print("\nThen install PyGObject in your virtual environment with:")
    print("pip install PyGObject")
    sys.exit(1)

import cv2
import numpy as np
from datetime import datetime
import cairo
from pathlib import Path

class ThermalWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("P2 Pro Thermal")
        self.fullscreen()

        # Main vertical box
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.box)

        # Camera view area
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_draw_func(self.draw_frame)
        self.box.append(self.drawing_area)

        # Button bar at bottom
        button_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_bar.set_spacing(10)
        button_bar.set_margin_start(10)
        button_bar.set_margin_end(10)
        button_bar.set_margin_bottom(10)

        # Large touch-friendly capture button
        capture_button = Gtk.Button(label="Capture")
        capture_button.connect("clicked", self.capture_image)
        capture_button.set_vexpand(False)
        capture_button.set_hexpand(True)
        button_bar.append(capture_button)

        # Color palette selector
        palette_store = Gtk.StringList()
        for name in ["Iron", "Rainbow", "Gray"]:
            palette_store.append(name)
        self.palette_dropdown = Gtk.DropDown(model=palette_store)
        self.palette_dropdown.connect("notify::selected", self.change_palette)
        self.palette_dropdown.set_vexpand(False)
        self.palette_dropdown.set_hexpand(True)
        button_bar.append(self.palette_dropdown)
        self.box.append(button_bar)

        # Initialize camera
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Failed to open camera")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 192)
        except Exception as e:
            print(f"Error initializing camera: {e}")
            print("Check if the camera is connected and you have permission to access it")
            print("You might need: sudo usermod -a -G video $USER")
            sys.exit(1)

        self.current_palette = cv2.COLORMAP_JET
        self.current_frame = None

        # Update frame every 40ms (25 FPS)
        GLib.timeout_add(40, self.update_frame)

    def update_frame(self):
        try:
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                colored = cv2.applyColorMap(gray, self.current_palette)
                self.current_frame = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
                self.drawing_area.queue_draw()
            return True
        except Exception as e:
            print(f"Error updating frame: {e}")
            return False

    def draw_frame(self, area, ctx, width, height):
        if self.current_frame is None:
            return

        scale = min(width / self.current_frame.shape[1],
                   height / self.current_frame.shape[0])

        new_width = int(self.current_frame.shape[1] * scale)
        new_height = int(self.current_frame.shape[0] * scale)

        x_offset = (width - new_width) // 2
        y_offset = (height - new_height) // 2

        surface = cairo.ImageSurface.create_for_data(
            self.current_frame.tobytes(),
            cairo.FORMAT_RGB24,
            self.current_frame.shape[1],
            self.current_frame.shape[0],
            self.current_frame.shape[1] * 4
        )

        ctx.save()
        ctx.translate(x_offset, y_offset)
        ctx.scale(scale, scale)
        ctx.set_source_surface(surface, 0, 0)
        ctx.paint()
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
        selected = dropdown.get_selected()
        self.current_palette = palette_map[selected]

    def do_close_request(self):
        if self.cap is not None:
            self.cap.release()
        return False

class ThermalApp(Gtk.Application):
    def __init__(self):
        super().__init__()

    def do_activate(self):
        win = ThermalWindow(self)
        win.present()

if __name__ == "__main__":
    app = ThermalApp()
    app.run(None)