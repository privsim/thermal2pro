"""Live view mode implementation."""
import os
import gi
try:
    gi.require_version('Gtk', os.environ.get('GTK_VERSION', '3.0'))
except ValueError:
    gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import logging
import cv2
import numpy as np
from .base_mode import BaseMode

logger = logging.getLogger(__name__)

# OpenCV colormap constants
COLORMAP_IRON = cv2.COLORMAP_HOT    # 11
COLORMAP_RAINBOW = cv2.COLORMAP_JET  # 2
COLORMAP_GRAY = cv2.COLORMAP_BONE   # 3

class LiveViewMode(BaseMode):
    """Real-time thermal camera display mode."""
    
    def __init__(self, window):
        """Initialize live view mode.
        
        Args:
            window: Parent ThermalWindow instance
        """
        # Initialize instance variables before super().__init__
        self.fps_overlay = True
        self.color_palette = COLORMAP_RAINBOW  # Start with rainbow (JET) palette
        self.frame_count = 0
        self.last_fps_time = 0
        self.current_fps = 0
        self.fps_button = None
        self.palette_dropdown = None
        
        super().__init__(window)
    
    def create_controls(self):
        """Create live view controls."""
        self.controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.controls_box.set_margin_top(5)
        self.controls_box.set_margin_bottom(5)
        if Gtk._version.startswith('4'):
            self.controls_box.set_margin_start(5)
            self.controls_box.set_margin_end(5)
        else:
            self.controls_box.set_margin_left(5)
            self.controls_box.set_margin_right(5)
        
        # Palette selector
        if Gtk._version.startswith('4'):
            palette_store = Gtk.StringList()
            for name in ["Iron", "Rainbow", "Gray"]:
                palette_store.append(name)
            self.palette_dropdown = Gtk.DropDown(model=palette_store)
            # Set initial selection to Rainbow
            self.palette_dropdown.set_selected(1)
        else:
            palette_store = Gtk.ListStore(str)
            for name in ["Iron", "Rainbow", "Gray"]:
                palette_store.append([name])
            self.palette_dropdown = Gtk.ComboBox.new_with_model(palette_store)
            renderer_text = Gtk.CellRendererText()
            self.palette_dropdown.pack_start(renderer_text, True)
            self.palette_dropdown.add_attribute(renderer_text, "text", 0)
            # Set initial selection to Rainbow
            self.palette_dropdown.set_active(1)
        
        # Enable input handling for dropdown
        self.palette_dropdown.set_can_focus(True)
        if not Gtk._version.startswith('4'):
            self.palette_dropdown.set_can_default(True)
        
        self.palette_dropdown.connect("changed" if Gtk._version.startswith('3') else "notify::selected", 
                                    self.on_palette_changed)
        
        # Make dropdown larger and more touch-friendly
        self.palette_dropdown.set_size_request(120, 40)
        
        # FPS toggle button
        self.fps_button = Gtk.ToggleButton(label="FPS")
        self.fps_button.set_can_focus(True)
        if not Gtk._version.startswith('4'):
            self.fps_button.set_can_default(True)
        self.fps_button.set_active(self.fps_overlay)
        self.fps_button.connect("toggled", self.on_fps_toggled)
        
        # Make button larger and more touch-friendly
        self.fps_button.set_size_request(80, 40)
        
        # Add controls to box with proper spacing
        if Gtk._version.startswith('4'):
            self.controls_box.append(self.palette_dropdown)
            self.controls_box.append(self.fps_button)
        else:
            self.controls_box.pack_start(self.palette_dropdown, True, True, 5)
            self.controls_box.pack_start(self.fps_button, False, False, 5)
        
        # Show all controls
        self.controls_box.show_all()
    
    def process_frame(self, frame):
        """Process camera frame.
        
        Args:
            frame: BGR format frame from camera
            
        Returns:
            Processed RGB frame
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply color palette
            colored = cv2.applyColorMap(gray, self.color_palette)
            
            # Convert to RGB for display
            rgb = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
            
            # Update FPS calculation
            self.frame_count += 1
            current_time = GLib.get_monotonic_time() / 1000000  # Convert to seconds
            if current_time - self.last_fps_time >= 1.0:
                self.current_fps = self.frame_count / (current_time - self.last_fps_time)
                self.frame_count = 0
                self.last_fps_time = current_time
            
            return rgb
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return frame  # Return original frame on error
    
    def draw_overlay(self, ctx, width, height):
        """Draw mode overlay.
        
        Args:
            ctx: Cairo context
            width: Drawing area width
            height: Drawing area height
        """
        if self.fps_overlay:
            # Draw FPS counter
            ctx.save()
            ctx.set_source_rgba(0, 0, 0, 0.7)
            ctx.rectangle(10, 10, 100, 30)
            ctx.fill()
            
            ctx.set_source_rgb(1, 1, 1)
            ctx.select_font_face("monospace")
            ctx.set_font_size(14)
            ctx.move_to(20, 30)
            ctx.show_text(f"FPS: {self.current_fps:.1f}")
            
            ctx.restore()
    
    def on_palette_changed(self, dropdown, *args):
        """Handle palette selection change."""
        palette_map = {
            0: COLORMAP_IRON,    # Iron
            1: COLORMAP_RAINBOW, # Rainbow
            2: COLORMAP_GRAY     # Gray
        }
        if Gtk._version.startswith('4'):
            selected = dropdown.get_selected()
        else:
            selected = dropdown.get_active()
        self.color_palette = palette_map[selected]
        logger.debug(f"Color palette changed to: {selected}")
    
    def on_fps_toggled(self, button):
        """Handle FPS overlay toggle."""
        self.fps_overlay = button.get_active()
        logger.debug(f"FPS overlay {'enabled' if self.fps_overlay else 'disabled'}")
    
    def _on_activate(self):
        """Handle mode activation."""
        # Reset FPS calculation
        self.frame_count = 0
        self.last_fps_time = GLib.get_monotonic_time() / 1000000
        self.current_fps = 0
    
    def _on_deactivate(self):
        """Handle mode deactivation."""
        pass
    
    def handle_key_press(self, keyval):
        """Handle key press events.
        
        Args:
            keyval: Key value from Gdk.EventKey
            
        Returns:
            True if key was handled, False otherwise
        """
        # F key toggles FPS overlay
        if keyval == ord('f') or keyval == ord('F'):
            self.fps_button.set_active(not self.fps_overlay)
            return True
        return False