import pytest
import numpy as np
import cairo
import ctypes
from thermal2pro.ui.cairo_handler import CairoSurfaceHandler

@pytest.fixture
def rgb_frame():
    # Create test frame that simulates camera output (RGB)
    frame = np.zeros((192, 256, 3), dtype=np.uint8)
    frame[:, :, 0] = np.linspace(0, 255, 256).reshape(1, -1)  # Red gradient
    frame[:, :, 1] = np.linspace(0, 255, 192).reshape(-1, 1)  # Green gradient
    frame[:, :, 2] = 128  # Blue constant
    # Ensure the array is contiguous and aligned
    return np.ascontiguousarray(frame)

def test_surface_creation_with_camera_frame(rgb_frame):
    # Test creating surface from a frame similar to what the camera produces
    try:
        surface = CairoSurfaceHandler.create_surface_from_frame(rgb_frame)
        assert isinstance(surface, cairo.ImageSurface)
        assert surface.get_width() == 256
        assert surface.get_height() == 192
        # Check if the surface is writable
        ctx = cairo.Context(surface)
        ctx.set_source_rgb(1.0, 0.0, 0.0)
        ctx.rectangle(0, 0, 10, 10)
        ctx.fill()
    except Exception as e:
        pytest.fail(f"Failed to create writable surface: {e}")

def test_frame_data_lifetime():
    # Create frame that will go out of scope
    frame = np.zeros((192, 256, 3), dtype=np.uint8)
    frame_copy = np.ascontiguousarray(frame.copy())
    
    # Get the data pointer before creating surface
    data_ptr = frame_copy.ctypes.data
    
    surface = CairoSurfaceHandler.create_surface_from_frame(frame_copy)
    
    # Force a garbage collection
    import gc
    gc.collect()
    
    # Try to write to the surface
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(1.0, 0.0, 0.0)
    ctx.paint()
    
    # The data should still be valid
    assert frame_copy.ctypes.data == data_ptr

def test_frame_memory_alignment():
    # Test with different frame configurations
    frame = np.zeros((192, 256, 3), dtype=np.uint8)
    frame = np.ascontiguousarray(frame)
    
    # Verify memory alignment
    assert frame.flags.c_contiguous, "Array must be C-contiguous"
    assert frame.flags.aligned, "Array must be aligned"
    assert frame.strides[0] % 4 == 0, "Stride must be 4-byte aligned"
    
    # This should work without errors
    surface = CairoSurfaceHandler.create_surface_from_frame(frame)
    assert isinstance(surface, cairo.ImageSurface)

def test_cairo_write_access():
    # Create a frame
    frame = np.zeros((192, 256, 3), dtype=np.uint8)
    frame = np.ascontiguousarray(frame)
    
    # Create surface
    surface = CairoSurfaceHandler.create_surface_from_frame(frame)
    
    # Attempt to write to it
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(1.0, 0.0, 0.0)
    ctx.rectangle(0, 0, 50, 50)
    try:
        ctx.fill()
    except Exception as e:
        pytest.fail(f"Failed to write to surface: {e}")
