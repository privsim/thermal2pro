"""Tests for the mode management system."""
import os
import gi
try:
    gi.require_version('Gtk', os.environ.get('GTK_VERSION', '3.0'))
except ValueError:
    gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2

from thermal2pro.ui.modes import AppMode, BaseMode, LiveViewMode
from thermal2pro.camera.mock_camera import MockThermalCamera

# Mock GTK widgets
class MockBox(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.children = []
        self.visible = False
    
    def append(self, child):
        self.children.append(child)
    
    def pack_start(self, child, *args, **kwargs):
        self.children.append(child)
    
    def show_all(self):
        self.visible = True
        for child in self.children:
            if hasattr(child, 'show_all'):
                child.show_all()

class MockButton(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visible = False
        self._active = True
    
    def get_active(self):
        return self._active
    
    def set_active(self, value):
        self._active = value
    
    def show_all(self):
        self.visible = True

class MockComboBox(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visible = False
        self.model = None
        self._active = 0
    
    def get_active(self):
        return self._active
    
    def set_active(self, value):
        self._active = value
    
    def get_selected(self):
        return self._active
    
    def set_selected(self, value):
        self._active = value
    
    @staticmethod
    def new_with_model(model):
        combo = MockComboBox()
        combo.model = model
        return combo
    
    def show_all(self):
        self.visible = True

class MockListStore(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        self.column_types = args if args else [str]
    
    def append(self, row):
        if isinstance(row, list):
            self.data.append(row)
        else:
            self.data.append([row])

class MockApplicationWindow(MagicMock):
    def __init__(self, *args, **kwargs):
        kwargs.pop('application', None)  # Remove application kwarg
        super().__init__(*args, **kwargs)
        self.controls_container = MockBox()
        self.set_title = MagicMock()
        self.set_default_size = MagicMock()
        self.set_position = MagicMock()
        self.present = MagicMock()
        self.add = MagicMock()
        self.set_child = MagicMock()
        self.__class__ = Gtk.ApplicationWindow

class TestModeImpl(BaseMode):
    """Test mode implementation."""
    def __init__(self, window):
        # Set up test flags before super().__init__
        self.create_controls_called = False
        self.process_frame_called = False
        self.draw_overlay_called = False
        self.on_activate_called = False
        self.on_deactivate_called = False
        self.cleanup_called = False
        super().__init__(window)
    
    def create_controls(self):
        """Create test controls."""
        self.controls_box = MockBox()
        self.create_controls_called = True
    
    def process_frame(self, frame):
        """Process test frame."""
        self.process_frame_called = True
        return frame
    
    def draw_overlay(self, ctx, width, height):
        """Draw test overlay."""
        self.draw_overlay_called = True
    
    def _on_activate(self):
        """Handle test activation."""
        self.on_activate_called = True
    
    def _on_deactivate(self):
        """Handle test deactivation."""
        self.on_deactivate_called = True
    
    def cleanup(self):
        """Clean up test mode."""
        self.cleanup_called = True
        super().cleanup()

@pytest.fixture
def mock_gtk():
    """Mock GTK widgets."""
    gtk_mocks = {
        'Box': MockBox,
        'Button': MockButton,
        'ToggleButton': MockButton,
        'ComboBox': MockComboBox,
        'ListStore': MockListStore,
        'CellRendererText': MagicMock,
        'ApplicationWindow': MockApplicationWindow,
        'Orientation': MagicMock(HORIZONTAL=0, VERTICAL=1),
        'WindowPosition': MagicMock(CENTER=1),
    }
    
    with patch.multiple('gi.repository.Gtk', **gtk_mocks):
        yield

@pytest.fixture
def mock_app():
    """Create a mock GTK application."""
    app = MagicMock()
    app.__class__ = Gtk.Application
    app.__gtype__ = GObject.GType(Gtk.Application)
    return app

@pytest.fixture
def mock_window():
    """Create a mock window."""
    return MockApplicationWindow()

@pytest.fixture
def test_mode(mock_window, mock_gtk):
    """Create a test mode instance."""
    return TestModeImpl(mock_window)

def test_mode_lifecycle(test_mode):
    """Test mode lifecycle (activation, deactivation, cleanup)."""
    # Test initial state
    assert not test_mode.is_active
    assert test_mode.create_controls_called
    
    # Test activation
    test_mode.activate()
    assert test_mode.is_active
    assert test_mode.on_activate_called
    assert test_mode.controls_box.visible
    
    # Test deactivation
    test_mode.deactivate()
    assert not test_mode.is_active
    assert test_mode.on_deactivate_called
    
    # Test cleanup
    test_mode.cleanup()
    assert test_mode.cleanup_called
    assert not test_mode.is_active

def test_live_view_mode(mock_window, mock_gtk):
    """Test LiveViewMode functionality."""
    mode = LiveViewMode(mock_window)
    
    # Test initialization
    assert not mode.is_active
    assert mode.fps_overlay
    assert mode.color_palette == cv2.COLORMAP_JET
    
    # Test activation
    mode.activate()
    assert mode.is_active
    assert mode.controls_box.visible
    
    # Test frame processing
    frame = np.zeros((192, 256, 3), dtype=np.uint8)
    processed = mode.process_frame(frame)
    assert processed.shape == frame.shape
    
    # Test palette switching
    mode.palette_dropdown.set_active(1)
    mode.on_palette_changed(mode.palette_dropdown)
    assert mode.color_palette == cv2.COLORMAP_JET
    
    # Test FPS toggle
    mode.fps_button.set_active(False)
    mode.on_fps_toggled(mode.fps_button)
    assert not mode.fps_overlay
    
    # Test cleanup
    mode.cleanup()
    assert not mode.is_active

def test_mode_switching(mock_app, mock_gtk):
    """Test mode switching in window."""
    with patch('thermal2pro.ui.window.MockThermalCamera') as mock_camera:
        # Create window with mock camera
        from thermal2pro.ui.window import ThermalWindow
        window = ThermalWindow(mock_app, use_mock_camera=True)
        
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

def test_frame_processing(mock_window, mock_gtk):
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

def test_error_handling(mock_window, mock_gtk):
    """Test error handling in modes."""
    mode = LiveViewMode(mock_window)
    
    # Test invalid frame
    invalid_frame = np.zeros((100, 100), dtype=np.uint8)  # Wrong shape
    processed = mode.process_frame(invalid_frame)
    assert processed is not None  # Should handle error gracefully
    
    # Test cleanup with error
    mock_window.controls_container.remove.side_effect = Exception("Test error")
    mode.cleanup()  # Should not raise exception