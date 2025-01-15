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
        assert isinstance(surface.surface, cairo.ImageSurface)
        assert surface.get_width() == 256
        assert surface.get_height() == 192
        # Check if the surface is writable
        ctx = cairo.Context(surface.surface)
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
    ctx = cairo.Context(surface.surface)
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
    assert isinstance(surface.surface, cairo.ImageSurface)

def test_cairo_write_access():
    # Create a frame
    frame = np.zeros((192, 256, 3), dtype=np.uint8)
    frame = np.ascontiguousarray(frame)
    
    # Create surface
    surface = CairoSurfaceHandler.create_surface_from_frame(frame)
    
    # Attempt to write to it
    ctx = cairo.Context(surface.surface)
    ctx.set_source_rgb(1.0, 0.0, 0.0)
    ctx.rectangle(0, 0, 50, 50)
    try:
        ctx.fill()
    except Exception as e:
        pytest.fail(f"Failed to write to surface: {e}")

def test_invalid_frame_input():
    # Test None input
    with pytest.raises(ValueError, match="Invalid frame"):
        CairoSurfaceHandler.create_surface_from_frame(None)
    
    # Test non-numpy array input
    with pytest.raises(ValueError, match="Invalid frame"):
        CairoSurfaceHandler.create_surface_from_frame([1, 2, 3])
    
    # Test empty numpy array
    with pytest.raises(ValueError, match="Invalid frame"):
        CairoSurfaceHandler.create_surface_from_frame(np.array([]))
    
    # Test 1D array
    with pytest.raises(ValueError, match="Invalid frame"):
        CairoSurfaceHandler.create_surface_from_frame(np.array([1, 2, 3]))

def test_alpha_channel_handling(rgb_frame):
    surface = CairoSurfaceHandler.create_surface_from_frame(rgb_frame)
    
    # Get the surface data
    surface_data = surface.get_data()
    # Convert to numpy array for easier inspection
    surface_array = np.frombuffer(surface_data, dtype=np.uint8)
    surface_array = surface_array.reshape(192, 256, 4)
    
    # Check that alpha channel is set to 255 (fully opaque)
    assert np.all(surface_array[:, :, 3] == 255), "Alpha channel should be 255"

def test_memory_cleanup():
    frame = np.zeros((192, 256, 3), dtype=np.uint8)
    surface = CairoSurfaceHandler.create_surface_from_frame(frame)
    surface_id = surface.surface_id
    
    # Verify the reference is stored
    assert surface_id in CairoSurfaceHandler._data_refs
    
    # Delete the surface and force garbage collection
    del surface
    import gc
    gc.collect()
    
    # Verify the reference is cleaned up
    assert surface_id not in CairoSurfaceHandler._data_refs

def test_scale_and_center():
    # Create a test surface
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    surface = CairoSurfaceHandler.create_surface_from_frame(frame)
    
    # Create a target surface that's larger
    target_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
    ctx = cairo.Context(target_surface)
    
    # Test scaling up
    CairoSurfaceHandler.scale_and_center(ctx, surface, 400, 300)
    
    # Test with None surface (should not raise any exceptions)
    CairoSurfaceHandler.scale_and_center(ctx, None, 400, 300)

def test_scale_and_center_smaller_target():
    # Create a test surface
    frame = np.zeros((400, 600, 3), dtype=np.uint8)
    surface = CairoSurfaceHandler.create_surface_from_frame(frame)
    
    # Create a target surface that's smaller
    target_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 150)
    ctx = cairo.Context(target_surface)
    
    # Test scaling down
    CairoSurfaceHandler.scale_and_center(ctx, surface, 200, 150)

def test_scale_and_center_edge_cases():
    # Create a test surface
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    surface = CairoSurfaceHandler.create_surface_from_frame(frame)
    target_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
    ctx = cairo.Context(target_surface)
    
    # Test with zero dimensions (should handle gracefully)
    CairoSurfaceHandler.scale_and_center(ctx, surface, 0, 300)
    CairoSurfaceHandler.scale_and_center(ctx, surface, 400, 0)
    CairoSurfaceHandler.scale_and_center(ctx, surface, 0, 0)
    
    # Test with very small dimensions
    CairoSurfaceHandler.scale_and_center(ctx, surface, 1, 1)
    
    # Test with very large dimensions
    CairoSurfaceHandler.scale_and_center(ctx, surface, 1000000, 1000000)

def test_scale_and_center_invalid_matrix():
    # Create a test surface
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    surface = CairoSurfaceHandler.create_surface_from_frame(frame)
    target_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
    ctx = cairo.Context(target_surface)
    
    # Test with dimensions that could cause matrix issues
    CairoSurfaceHandler.scale_and_center(ctx, surface, float('inf'), 300)
    CairoSurfaceHandler.scale_and_center(ctx, surface, 400, float('inf'))
    CairoSurfaceHandler.scale_and_center(ctx, surface, float('nan'), 300)
    CairoSurfaceHandler.scale_and_center(ctx, surface, 400, float('nan'))
