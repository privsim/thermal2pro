"""Tests for the mode management system."""
from gi.repository import Gtk, Gio, GObject
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2

from thermal2pro.ui.modes import AppMode, BaseMode, LiveViewMode
from thermal2pro.camera.mock_camera import MockThermalCamera
from thermal2pro.ui.window import ThermalWindow

class TestThermalWindow(ThermalWindow):
    """Test version of ThermalWindow that uses mock widgets."""
    def __init__(self, app, use_mock_camera=False):
        # Create mock widgets before super().__init__
        self.box = Gtk.Box()
        self.drawing_area = Gtk.DrawingArea()
        self.controls_container = Gtk.Box()
        
        # Initialize window
        super().__init__(app, use_mock_camera)

class TestModes:
    """Test mode functionality."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a mock window."""
        window = MagicMock()
        window.controls_container = Gtk.Box()
        window.controls_container.pack_start = MagicMock()
        window.controls_container.remove = MagicMock()
        window.controls_container.show_all = MagicMock()
        return window

    @pytest.fixture
    def test_mode(self, mock_window):
        """Create a test mode instance."""
        class TestModeImpl(BaseMode):
            def __init__(self, window):
                self.create_controls_called = False
                self.process_frame_called = False
                self.draw_overlay_called = False
                self.on_activate_called = False
                self.on_deactivate_called = False
                self.cleanup_called = False
                super().__init__(window)
            
            def create_controls(self):
                self.controls_box = Gtk.Box()
                self.controls_box.show_all = MagicMock()
                self.create_controls_called = True
            
            def process_frame(self, frame):
                self.process_frame_called = True
                return frame
            
            def draw_overlay(self, ctx, width, height):
                self.draw_overlay_called = True
            
            def _on_activate(self):
                self.on_activate_called = True
            
            def _on_deactivate(self):
                self.on_deactivate_called = True
            
            def cleanup(self):
                self.cleanup_called = True
                super().cleanup()
        
        return TestModeImpl(mock_window)

    def test_mode_lifecycle(self, test_mode):
        """Test mode lifecycle (activation, deactivation, cleanup)."""
        # Test initial state
        assert not test_mode.is_active
        assert test_mode.create_controls_called
        
        # Test activation
        test_mode.activate()
        assert test_mode.is_active
        assert test_mode.on_activate_called
        assert test_mode.controls_box.show_all.called
        
        # Test deactivation
        test_mode.deactivate()
        assert not test_mode.is_active
        assert test_mode.on_deactivate_called
        
        # Test cleanup
        test_mode.cleanup()
        assert test_mode.cleanup_called
        assert not test_mode.is_active

    def test_live_view_mode(self, mock_window):
        """Test LiveViewMode functionality."""
        mode = LiveViewMode(mock_window)
        
        # Test initialization
        assert not mode.is_active
        assert mode.fps_overlay
        assert mode.color_palette == cv2.COLORMAP_JET
        
        # Test activation
        mode.activate()
        assert mode.is_active
        
        # Test frame processing
        frame = np.zeros((192, 256, 3), dtype=np.uint8)
        processed = mode.process_frame(frame)
        assert processed.shape == frame.shape
        
        # Test palette switching
        mode.palette_dropdown = MagicMock()
        mode.palette_dropdown.get_active.return_value = 1
        mode.on_palette_changed(mode.palette_dropdown)
        assert mode.color_palette == cv2.COLORMAP_JET
        
        # Test FPS toggle
        mode.fps_button = MagicMock()
        mode.fps_button.get_active.return_value = False
        mode.on_fps_toggled(mode.fps_button)
        assert not mode.fps_overlay
        
        # Test cleanup
        mode.cleanup()
        assert not mode.is_active

    def test_mode_switching(self, mock_app):
        """Test mode switching in window."""
        with patch('thermal2pro.ui.window.MockThermalCamera'):
            # Create window with mock camera
            window = TestThermalWindow(mock_app, use_mock_camera=True)
            
            try:
                # Verify initial mode
                assert window.current_mode == AppMode.LIVE_VIEW
                assert window.modes[AppMode.LIVE_VIEW].is_active
                
                # Test mode button toggling
                for mode in AppMode:
                    if mode in window.modes:
                        button = window.mode_buttons[mode]
                        button.set_active(True)
                        window.on_mode_button_toggled(button, mode)
                        assert window.current_mode == mode
                        assert window.modes[mode].is_active
            finally:
                window.destroy()

    def test_frame_processing(self, mock_window):
        """Test frame processing through modes."""
        mode = LiveViewMode(mock_window)
        mode.activate()
        
        # Create test frame
        frame = np.zeros((192, 256, 3), dtype=np.uint8)
        frame[50:150, 50:150] = 255  # Add white square
        
        # Process frame
        processed = mode.process_frame(frame)
        
        # Verify processing
        assert processed.shape == frame.shape
        assert np.any(processed != frame)  # Should be different due to colormap

    def test_error_handling(self, mock_window):
        """Test error handling in modes."""
        mode = LiveViewMode(mock_window)
        
        # Test invalid frame
        invalid_frame = np.zeros((100, 100), dtype=np.uint8)  # Wrong shape
        processed = mode.process_frame(invalid_frame)
        assert processed is not None  # Should handle error gracefully
        
        # Test cleanup with error
        mock_window.controls_container.remove.side_effect = Exception("Test error")
        mode.cleanup()  # Should not raise exception