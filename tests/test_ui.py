"""Tests for UI components."""
import os
import gi
import sys

# Get GTK version from environment or use system default
GTK_VERSION = os.environ.get('GTK_VERSION', '4.0')
gi.require_version('Gtk', GTK_VERSION)

from gi.repository import Gtk, GLib, Gdk
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2

from thermal2pro.ui.window import ThermalWindow
from thermal2pro.camera.mock_camera import MockThermalCamera

@pytest.fixture
def mock_app():
    """Create a mock GTK application."""
    app = MagicMock()
    app.__class__ = Gtk.Application
    return app

@pytest.fixture
def mock_camera():
    """Create a mock thermal camera."""
    camera = MockThermalCamera()
    return camera

def test_window_initialization(mock_app):
    """Test window initialization."""
    window = ThermalWindow(mock_app, use_mock_camera=True)
    assert window is not None
    assert isinstance(window, Gtk.ApplicationWindow)
    assert window.get_title() == "P2 Pro Thermal"

def test_camera_fallback(mock_app):
    """Test camera initialization fallback."""
    with patch('cv2.VideoCapture') as mock_cv2:
        # Make real camera fail
        mock_cv2.return_value.isOpened.return_value = False
        
        # Should fall back to mock camera
        window = ThermalWindow(mock_app, use_mock_camera=False)
        assert window.cap is not None
        assert isinstance(window.cap, MockThermalCamera)

def test_frame_processing(mock_app):
    """Test frame processing pipeline."""
    window = ThermalWindow(mock_app, use_mock_camera=True)
    
    # Create test frame
    frame = np.zeros((192, 256, 3), dtype=np.uint8)
    frame[50:150, 50:150] = 255  # Add white square
    
    # Mock camera read
    window.cap.read = MagicMock(return_value=(True, frame))
    
    # Process frame
    assert window.update_frame()
    assert window.current_frame is not None
    assert window.current_frame.shape == frame.shape

def test_window_cleanup(mock_app):
    """Test window cleanup."""
    window = ThermalWindow(mock_app, use_mock_camera=True)
    
    # Mock camera
    window.cap = MagicMock()
    
    # Trigger cleanup
    window.do_close_request()
    
    # Verify camera released
    window.cap.release.assert_called_once()

def test_drawing_area(mock_app):
    """Test drawing area setup."""
    window = ThermalWindow(mock_app, use_mock_camera=True)
    
    # Verify drawing area properties
    assert window.drawing_area is not None
    assert isinstance(window.drawing_area, Gtk.DrawingArea)
    assert window.drawing_area.get_vexpand()
    assert window.drawing_area.get_hexpand()

def test_error_handling(mock_app):
    """Test error handling in frame processing."""
    window = ThermalWindow(mock_app, use_mock_camera=True)
    
    # Make camera read fail
    window.cap.read = MagicMock(return_value=(False, None))
    
    # Should handle error gracefully
    assert window.update_frame()  # Returns True to continue updates
    assert window.current_frame is None
