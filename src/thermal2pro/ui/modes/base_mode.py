"""Base mode implementation."""
from gi.repository import Gtk

class BaseMode:
    """Base class for application modes."""
    
    def __init__(self, window):
        """Initialize mode.
        
        Args:
            window: Parent window
        """
        self.window = window
        self.is_active = False
        self.controls_box = None
        self.create_controls()
        
    def create_controls(self):
        """Create mode-specific controls.
        
        Override in subclasses to create mode-specific controls.
        Must set self.controls_box.
        """
        raise NotImplementedError
        
    def process_frame(self, frame):
        """Process incoming frame.
        
        Args:
            frame: Input frame
            
        Returns:
            Processed frame
        """
        raise NotImplementedError
        
    def draw_overlay(self, ctx, width, height):
        """Draw mode overlay.
        
        Args:
            ctx: Cairo context
            width: Surface width
            height: Surface height
        """
        pass
        
    def activate(self):
        """Activate mode."""
        if self.is_active:
            return
            
        self.is_active = True
        
        # Add controls to window
        if self.controls_box:
            self.window.controls_container.append(self.controls_box)
            self.controls_box.set_visible(True)
        
        self._on_activate()
        
    def deactivate(self):
        """Deactivate mode."""
        if not self.is_active:
            return
            
        self._on_deactivate()
        
        # Remove controls from window
        if self.controls_box:
            self.controls_box.set_visible(False)
            self.window.controls_container.remove(self.controls_box)
            
        self.is_active = False
        
    def _on_activate(self):
        """Handle mode activation.
        
        Override in subclasses for mode-specific activation.
        """
        pass
        
    def _on_deactivate(self):
        """Handle mode deactivation.
        
        Override in subclasses for mode-specific deactivation.
        """
        pass
        
    def cleanup(self):
        """Clean up mode resources."""
        if self.is_active:
            self.deactivate()