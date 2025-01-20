"""Tests for UI components."""
from gi.repository import Gtk, GLib, Gdk
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2

from thermal2pro.ui.window import ThermalWindow
from thermal2pro.camera.mock_camera import MockThermalCamera
from thermal2pro.ui.cairo_handler import CairoSurfaceHandler

class TestThermalWindow(ThermalWindow):
    """Test version of ThermalWindow."""
    def __init__(self, app, use_mock_camera=False):
        super().__init__(app)
        
        # Override camera creation for testing
        if use_mock_camera:
            self.cap = MockThermalCamera()
        else:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.cap = MockThermalCamera()

class TestWindow:
    """Test window functionality."""
    
    def test_window_initialization(self, mock_app):
        """Test window initialization."""
        with patch('thermal2pro.ui.window.MockThermalCamera'):
            window = TestThermalWindow(mock_app, use_mock_camera=True)
            assert isinstance(window, Gtk.ApplicationWindow)
            assert window.get_title() == "P2 Pro Thermal"
            window.close()
            window.destroy()

    def test_camera_fallback(self, mock_app):
        """Test camera initialization fallback."""
        with patch('cv2.VideoCapture') as mock_cv2:
            # Make real camera fail
            mock_cv2.return_value.isOpened.return_value = False
            
            # Should fall back to mock camera
            window = TestThermalWindow(mock_app, use_mock_camera=False)
            assert isinstance(window.cap, MockThermalCamera)
            window.close()
            window.destroy()

    def test_frame_processing(self, mock_app):
        """Test frame processing pipeline."""
        with patch('thermal2pro.ui.window.MockThermalCamera'):
            window = TestThermalWindow(mock_app, use_mock_camera=True)
            
            # Create test frame
            frame = np.zeros((192, 256), dtype=np.uint8)  # Grayscale frame
            frame[50:150, 50:150] = 255  # Add white square
            
            # Mock camera read
            window.cap.read = MagicMock(return_value=(True, frame))
            
            # Process frame
            assert window.update_frame()
            assert window.current_frame is not None
            assert window.current_frame.shape == (192, 256, 3)  # Should be RGB
            window.close()
            window.destroy()

    def test_window_cleanup(self, mock_app):
        """Test window cleanup."""
        with patch('thermal2pro.ui.window.MockThermalCamera'):
            window = TestThermalWindow(mock_app, use_mock_camera=True)
            
            # Mock camera
            window.cap = MagicMock()
            
            # Trigger cleanup
            window.close()
            
            # Verify camera released
            window.cap.release.assert_called_once()
            window.destroy()

    def test_drawing_area(self, mock_app):
        """Test drawing area setup."""
        with patch('thermal2pro.ui.window.MockThermalCamera'):
            window = TestThermalWindow(mock_app, use_mock_camera=True)
            
            # Verify drawing area properties
            assert window.drawing_area is not None
            assert isinstance(window.drawing_area, Gtk.DrawingArea)
            assert window.drawing_area.get_vexpand()
            assert window.drawing_area.get_hexpand()
            window.close()
            window.destroy()

    def test_error_handling(self, mock_app):
        """Test error handling in frame processing."""
        with patch('thermal2pro.ui.window.MockThermalCamera'):
            window = TestThermalWindow(mock_app, use_mock_camera=True)
            
            # Make camera read fail
            window.cap.read = MagicMock(return_value=(False, None))
            
            # Should handle error gracefully
            assert window.update_frame()  # Returns True to continue updates
            assert window.current_frame is None
            window.close()
            window.destroy()

    def test_resize_handling(self, mock_app):
        """Test window resize handling."""
        with patch('thermal2pro.ui.window.MockThermalCamera'):
            window = TestThermalWindow(mock_app, use_mock_camera=True)
            
            # Test resizing
            window.set_default_size(1024, 768)
            assert window.get_default_size() == (1024, 768)
            window.close()
            window.destroy()

    def test_mode_button_interaction(self, mock_app):
        """Test mode button interactions."""
        with patch('thermal2pro.ui.window.MockThermalCamera'):
            window = TestThermalWindow(mock_app, use_mock_camera=True)
            
            # Test mode switching
            for mode in window.mode_buttons:
                button = window.mode_buttons[mode]
                button.set_active(True)
                window.on_mode_button_toggled(button, mode)
                assert window.current_mode == mode
            
            window.close()
            window.destroy()