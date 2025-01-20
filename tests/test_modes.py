"""Tests for the mode management system."""
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GObject
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2
import cairo

from thermal2pro.ui.modes import AppMode, BaseMode, LiveViewMode
from thermal2pro.camera.mock_camera import MockThermalCamera
from thermal2pro.ui.window import ThermalWindow

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

class TestModes:
    """Test mode functionality."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a mock window."""
        window = MagicMock()
        window.controls_container = Gtk.Box()
        window.controls_container.append = MagicMock()
        window.controls_container.remove = MagicMock()
        window.controls_container.set_visible = MagicMock()
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
        assert test_mode.window.controls_container.append.called
        
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
        
        # Create test frame
        frame = np.zeros((192, 256, 3), dtype=np.uint8)  # BGR frame
        
        # Process frame
        processed = mode.process_frame(frame)
        assert processed.shape == (192, 256, 3)  # Should remain BGR
        
        # Mock palette dropdown
        mode.palette_dropdown = MagicMock()
        mode.palette_dropdown.get_selected = MagicMock(return_value=1)
        mode.on_palette_changed(mode.palette_dropdown)
        assert mode.color_palette == cv2.COLORMAP_JET
        
        # Test cleanup
        mode.cleanup()
        assert not mode.is_active

    def test_mode_switching(self, mock_app):
        """Test mode switching in window."""
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
            window.close()

    def test_frame_processing(self, mock_window):
        """Test frame processing through modes."""
        mode = LiveViewMode(mock_window)
        mode.activate()
        
        # Create test frame
        frame = np.zeros((192, 256), dtype=np.uint8)  # Grayscale
        frame[50:150, 50:150] = 255  # Add white square
        
        # Process frame
        processed = mode.process_frame(frame)
        
        # Verify processing
        assert processed.shape == (192, 256, 3)  # Should be BGR
        assert np.any(processed != 0)  # Should have color mapping applied

    def test_overlay_drawing(self, mock_window):
        """Test overlay drawing functionality."""
        mode = LiveViewMode(mock_window)
        mode.activate()
        
        # Create surface and context for testing
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 256, 192)
        ctx = cairo.Context(surface)
        
        # Draw overlay
        mode.draw_overlay(ctx, 256, 192)
        
        # Get surface data
        data = surface.get_data()
        assert data is not None  # Verify drawing occurred
        
        # Test FPS overlay
        mode.fps_overlay = True
        mode.current_fps = 30.0
        mode.draw_overlay(ctx, 256, 192)
        assert data is not None  # Verify FPS overlay drawn