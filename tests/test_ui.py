import pytest
import gi
import cairo
import numpy as np
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def test_cairo_surface_creation():
    # Create contiguous array with proper stride alignment
    test_frame = np.zeros((192, 256, 4), dtype=np.uint8)
    frame_data = np.ascontiguousarray(test_frame).copy()
    
    try:
        surface = cairo.ImageSurface.create_for_data(
            frame_data.data,
            cairo.FORMAT_RGB24,
            256,
            192,
            frame_data.strides[0]
        )
        assert surface is not None
    except BufferError as e:
        pytest.fail(f"Failed to create Cairo surface: {e}")
        
    # Verify surface properties
    assert surface.get_width() == 256
    assert surface.get_height() == 192
    assert surface.get_format() == cairo.FORMAT_RGB24

def test_frame_buffer_writable():
    test_frame = np.zeros((192, 256, 3), dtype=np.uint8)
    assert test_frame.flags.writeable
    
    frame_bytes = test_frame.tobytes()
    assert frame_bytes is not None
    assert len(frame_bytes) == 192 * 256 * 3

def test_gtk_drawing_area():
    win = Gtk.Window()
    drawing_area = Gtk.DrawingArea()
    win.add(drawing_area)
    assert drawing_area.get_allocated_width() >= 0
    assert drawing_area.get_allocated_height() >= 0
