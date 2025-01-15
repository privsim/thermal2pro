import cairo
import numpy as np
from typing import Dict, Optional
import gc

class CairoSurfaceHandler:
    # Class-level storage for data references
    _data_refs: Dict[int, np.ndarray] = {}
    
    @staticmethod
    def create_surface_from_frame(frame):
        """Create a Cairo surface from a numpy array frame."""
        if frame is None or not isinstance(frame, np.ndarray) or len(frame.shape) < 2:
            raise ValueError("Invalid frame")
            
        height, width = frame.shape[:2]
        
        # Create a writeable copy with proper memory layout
        frame_copy = np.zeros((height, width, 4), dtype=np.uint8)
        frame_copy[..., :3] = frame
        frame_copy[..., 3] = 255  # Alpha channel
        frame_copy = np.ascontiguousarray(frame_copy)
        
        stride = width * 4
        
        surface = cairo.ImageSurface.create_for_data(
            frame_copy.data,
            cairo.FORMAT_ARGB32,
            width,
            height,
            stride
        )
        
        # Store reference in class dict using surface address as key
        surface_id = id(surface)
        CairoSurfaceHandler._data_refs[surface_id] = frame_copy
        
        # Return a wrapped surface that will handle cleanup
        return _ManagedCairoSurface(surface, surface_id)
    
    @staticmethod
    def _cleanup_ref(surface_id):
        """Clean up the data reference for a given surface ID."""
        CairoSurfaceHandler._data_refs.pop(surface_id, None)
        
    @staticmethod
    def scale_and_center(ctx, surface, target_width, target_height):
        """Scale and center a surface in the given context."""
        if surface is None:
            return
            
        # If we have a managed surface, get the underlying cairo surface
        if isinstance(surface, _ManagedCairoSurface):
            surface = surface.surface
            
        scale = min(target_width / surface.get_width(),
                   target_height / surface.get_height())
                   
        new_width = int(surface.get_width() * scale)
        new_height = int(surface.get_height() * scale)
        
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        
        ctx.save()
        ctx.translate(x_offset, y_offset)
        ctx.scale(scale, scale)
        ctx.set_source_surface(surface, 0, 0)
        ctx.paint()
        ctx.restore()

class _ManagedCairoSurface:
    """A wrapper for cairo.ImageSurface that handles cleanup of numpy array data."""
    
    def __init__(self, surface: cairo.ImageSurface, surface_id: int):
        self.surface = surface
        self.surface_id = surface_id
        
    def __del__(self):
        """Clean up when the surface is garbage collected."""
        CairoSurfaceHandler._cleanup_ref(self.surface_id)
        
    def get_width(self):
        return self.surface.get_width()
        
    def get_height(self):
        return self.surface.get_height()
        
    def get_data(self):
        return self.surface.get_data()
