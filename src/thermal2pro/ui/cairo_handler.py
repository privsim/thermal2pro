import cairo
import numpy as np
from typing import Dict
import weakref

class CairoSurfaceHandler:
    # Class-level storage for data references
    _data_refs: Dict[int, np.ndarray] = {}
    
    @staticmethod
    def create_surface_from_frame(frame):
        if frame is None or not isinstance(frame, np.ndarray):
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
        CairoSurfaceHandler._data_refs[id(surface)] = frame_copy
        
        # Create finalizer to clean up reference when surface is destroyed
        weakref.finalize(surface, CairoSurfaceHandler._cleanup_ref, id(surface))
        
        return surface
    
    @staticmethod
    def _cleanup_ref(surface_id):
        CairoSurfaceHandler._data_refs.pop(surface_id, None)
        
    @staticmethod
    def scale_and_center(ctx, surface, target_width, target_height):
        if surface is None:
            return
            
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
