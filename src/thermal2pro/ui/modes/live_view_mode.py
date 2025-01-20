"""Live view mode implementation."""
from gi.repository import Gtk, GLib
import cv2
import numpy as np
import logging
from .base_mode import BaseMode
import cairo

logger = logging.getLogger(__name__)

class LiveViewMode(BaseMode):
    """Mode for displaying live thermal camera feed."""
    
    def __init__(self, window):
        super().__init__(window)
        self.fps_overlay = True
        self.color_palette = cv2.COLORMAP_JET
        self.frame_count = 0
        self.last_fps_update = GLib.get_monotonic_time()
        self.current_fps = 0
        
    def create_controls(self):
        """Create mode-specific controls."""
        self.controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.controls_box.set_spacing(10)
        
        # FPS overlay toggle
        self.fps_button = Gtk.ToggleButton(label="FPS Overlay")
        self.fps_button.set_active(True)
        self.fps_button.connect("toggled", self.on_fps_toggled)
        self.controls_box.append(self.fps_button)
        
        # Color palette selector
        palette_store = Gtk.StringList()
        for name in ["Iron", "Rainbow", "Gray"]:
            palette_store.append(name)
        self.palette_dropdown = Gtk.DropDown(model=palette_store)
        self.palette_dropdown.connect("notify::selected", self.on_palette_changed)
        self.controls_box.append(self.palette_dropdown)
        
    def process_frame(self, frame):
        """Process incoming frame.
        
        Args:
            frame: Input frame (grayscale or BGR)
            
        Returns:
            Processed frame (BGR)
        """
        try:
            # Update FPS counter
            self.frame_count += 1
            current_time = GLib.get_monotonic_time()
            time_elapsed = current_time - self.last_fps_update
            
            if time_elapsed >= 1000000:  # Update FPS every second
                self.current_fps = self.frame_count * 1000000 / time_elapsed
                self.frame_count = 0
                self.last_fps_update = current_time
            
            # Convert BGR to grayscale if needed
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            
            # Apply color mapping
            colored = cv2.applyColorMap(gray, self.color_palette)
            
            # Return as BGR (no need to convert)
            return colored
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return frame
    
    def draw_overlay(self, ctx: cairo.Context, width: int, height: int):
        """Draw mode overlay.
        
        Args:
            ctx: Cairo context
            width: Surface width
            height: Surface height
        """
        if not self.fps_overlay:
            return
            
        # Draw FPS counter
        ctx.set_source_rgb(1, 1, 1)
        ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(20)
        ctx.move_to(10, 30)
        ctx.show_text(f"FPS: {self.current_fps:.1f}")
    
    def on_fps_toggled(self, button):
        """Handle FPS overlay toggle."""
        self.fps_overlay = button.get_active()
        # Force redraw
        self.window.queue_draw()
    
    def on_palette_changed(self, dropdown, *args):
        """Handle palette selection change."""
        palette_map = {
            0: cv2.COLORMAP_HOT,    # Iron
            1: cv2.COLORMAP_JET,    # Rainbow
            2: cv2.COLORMAP_BONE    # Gray
        }
        selected = dropdown.get_selected()
        self.color_palette = palette_map[selected]
        # Force redraw
        self.window.queue_draw()