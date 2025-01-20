"""Tests for UI components."""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk

from thermal2pro.ui.window import ThermalWindow
from thermal2pro.ui.modes import AppMode
from thermal2pro.camera.mock_camera import MockThermalCamera

@pytest.fixture
def test_window(mock_app):
    """Create a test window fixture."""
    with patch('thermal2pro.ui.window.ThermalWindow._update_window_position'):
        window = ThermalWindow(mock_app)
        yield window
        window.close()
        window.destroy()

class TestWindow:
    """Test window functionality."""
    
    @pytest.mark.gtk
    def test_window_initialization(self, test_window):
        """Test window initialization."""
        assert isinstance(test_window, Gtk.ApplicationWindow)
        assert test_window.get_title() == "P2 Pro Thermal"

    @pytest.mark.gtk
    def test_camera_fallback(self, mock_app):
        """Test camera initialization fallback."""
        with patch('cv2.VideoCapture') as mock_cv2:
            # Make real camera fail
            mock_cv2.return_value.isOpened.return_value = False
            
            window = ThermalWindow(mock_app)
            try:
                assert isinstance(window.cap, MockThermalCamera)
            finally:
                window.close()
                window.destroy()

    @pytest.mark.gtk
    def test_frame_processing(self, test_window):
        """Test frame processing pipeline."""
        # Create test frame
        frame = np.zeros((192, 256), dtype=np.uint8)  # Grayscale frame
        frame[50:150, 50:150] = 255  # Add white square
        
        # Replace camera with MockThermalCamera instance
        mock_camera = MockThermalCamera()
        mock_camera.read = MagicMock(return_value=(True, frame))
        test_window.cap = mock_camera
        
        # Process frame
        assert test_window.update_frame()
        assert test_window.current_frame is not None
        assert test_window.current_frame.shape == (192, 256, 3)  # Should be RGB

    @pytest.mark.gtk
    def test_window_cleanup(self, test_window):
        """Test window cleanup."""
        # Use MockThermalCamera instead of generic MagicMock
        mock_camera = MockThermalCamera()
        mock_camera.release = MagicMock()
        test_window.cap = mock_camera
        
        # Trigger cleanup
        test_window.close()
        
        # Verify camera released
        mock_camera.release.assert_called_once()

    @pytest.mark.gtk
    def test_drawing_area(self, test_window):
        """Test drawing area setup."""
        # Verify drawing area properties
        assert test_window.drawing_area is not None
        assert isinstance(test_window.drawing_area, Gtk.DrawingArea)
        assert test_window.drawing_area.get_vexpand()
        assert test_window.drawing_area.get_hexpand()

    @pytest.mark.gtk
    def test_error_handling(self, test_window):
        """Test error handling in frame processing."""
        # Replace with MockThermalCamera
        mock_camera = MockThermalCamera()
        mock_camera.read = MagicMock(return_value=(False, None))
        test_window.cap = mock_camera
        
        # Should handle error gracefully
        assert test_window.update_frame()  # Returns True to continue updates
        assert test_window.current_frame is None

    @pytest.mark.gtk
    def test_resize_handling(self, test_window):
        """Test window resize handling."""
        # Test resizing
        test_window.set_default_size(1024, 768)
        assert test_window.get_default_size() == (1024, 768)

    @pytest.mark.gtk
    def test_mode_button_interaction(self, test_window):
        """Test mode button interactions."""
        # Test only available modes
        available_modes = [mode for mode in AppMode if mode in test_window.modes]
        
        # Get original mode
        initial_mode = test_window.current_mode
        assert initial_mode in available_modes
        assert test_window.modes[initial_mode].is_active
        
        # Test mode switching
        for mode in available_modes:
            button = test_window.mode_buttons[mode]
            button.set_active(True)
            test_window.on_mode_button_toggled(button, mode)
            assert test_window.current_mode == mode
            assert test_window.modes[mode].is_active
            
            # Verify other buttons are inactive
            for other_mode, other_button in test_window.mode_buttons.items():
                if other_mode != mode:
                    assert not other_button.get_active()
            
            # Test deactivation attempt (should stay active)
            button.set_active(False)
            test_window.on_mode_button_toggled(button, mode)
            assert test_window.current_mode == mode
            assert button.get_active()  # Button should stay active

    @pytest.mark.gtk
    def test_button_visual_properties(self, test_window):
        """Test button visual and interaction properties."""
        for mode, button in test_window.mode_buttons.items():
            # Check button properties
            assert button.get_size_request() == (120, 50)  # Touch-friendly size
            assert button.get_has_frame()  # Visual feedback enabled
            assert 'mode-button' in button.get_style_context().list_classes()

    @pytest.mark.gtk
    def test_mode_cleanup(self, test_window):
        """Test proper cleanup when switching modes."""
        # Switch to each mode and verify cleanup
        for mode in [m for m in AppMode if m in test_window.modes]:
            old_mode = test_window.current_mode
            old_mode_instance = test_window.modes[old_mode]
            
            # Switch mode
            button = test_window.mode_buttons[mode]
            button.set_active(True)
            test_window.on_mode_button_toggled(button, mode)
            
            # Verify old mode cleaned up
            assert not old_mode_instance.is_active
            assert not old_mode_instance.controls_box.get_visible()
            
            # Verify new mode properly initialized
            assert test_window.modes[mode].is_active
            assert test_window.modes[mode].controls_box.get_visible()