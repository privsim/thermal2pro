"""Base class for application modes."""
import os
import gi

# Import GTK after version is set in main.py
from gi.repository import Gtk, GLib, Gdk
import logging
from abc import ABC, abstractmethod
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class BaseMode(ABC):
    """Abstract base class for application modes."""
    
    def __init__(self, window):
        """Initialize mode.
        
        Args:
            window: Parent ThermalWindow instance
        """
        self.window = window
        self.controls_box = None
        self.is_active = False
        
        # Create mode-specific UI
        self.create_controls()
        logger.debug(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    def create_controls(self):
        """Create mode-specific UI controls.
        
        This method should create a Gtk.Box containing all mode-specific
        controls and store it in self.controls_box.
        """
        pass
    
    @abstractmethod
    def process_frame(self, frame):
        """Process a camera frame.
        
        Args:
            frame: numpy array containing the camera frame
            
        Returns:
            Processed frame as numpy array
        """
        pass
    
    def activate(self):
        """Activate this mode."""
        if not self.is_active:
            logger.info(f"Activating {self.__class__.__name__}")
            self.is_active = True
            if self.controls_box:
                # Add controls to window
                if Gtk._version.startswith('4'):
                    self.window.controls_container.append(self.controls_box)
                else:
                    self.window.controls_container.pack_start(self.controls_box, True, True, 0)
                
                # Enable input events
                if not Gtk._version.startswith('4'):
                    events = Gdk.EventMask.BUTTON_PRESS_MASK | \
                            Gdk.EventMask.BUTTON_RELEASE_MASK | \
                            Gdk.EventMask.POINTER_MOTION_MASK | \
                            Gdk.EventMask.TOUCH_MASK
                    self.controls_box.add_events(events)
                
                # Show controls
                self.controls_box.show_all()
                self.controls_box.set_can_focus(True)
                
            self._on_activate()
    
    def deactivate(self):
        """Deactivate this mode."""
        if self.is_active:
            logger.info(f"Deactivating {self.__class__.__name__}")
            self.is_active = False
            if self.controls_box:
                # Hide controls before removing
                self.controls_box.hide()
                if Gtk._version.startswith('4'):
                    self.window.controls_container.remove(self.controls_box)
                else:
                    self.window.controls_container.remove(self.controls_box)
            self._on_deactivate()
    
    def _on_activate(self):
        """Called when mode is activated.
        
        Override this in subclasses to perform mode-specific activation tasks.
        """
        pass
    
    def _on_deactivate(self):
        """Called when mode is deactivated.
        
        Override this in subclasses to perform mode-specific cleanup tasks.
        """
        pass
    
    def handle_key_press(self, keyval):
        """Handle key press events.
        
        Args:
            keyval: Key value from Gdk.EventKey
            
        Returns:
            True if key was handled, False otherwise
        """
        return False
    
    def update(self):
        """Update mode state.
        
        Called periodically by the main window. Override in subclasses
        to perform mode-specific updates.
        
        Returns:
            True to continue updates, False to stop
        """
        return True
    
    def draw_overlay(self, ctx, width, height):
        """Draw mode-specific overlay.
        
        Args:
            ctx: Cairo context
            width: Drawing area width
            height: Drawing area height
        """
        pass
    
    def cleanup(self):
        """Clean up mode resources.
        
        Called when mode is being destroyed. Override in subclasses
        to perform final cleanup.
        """
        self.deactivate()