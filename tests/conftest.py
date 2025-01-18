"""Test configuration and fixtures."""
import os
import gi

# Set GTK version before any imports
os.environ['GTK_VERSION'] = '3.0'
gi.require_version('Gtk', '3.0')

import pytest
from gi.repository import Gtk, GLib, Gdk, Gio
from unittest.mock import MagicMock, patch

class MockBox(Gtk.Box):
    """Mock Gtk.Box that satisfies type checking."""
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.children = []
        self.visible = False
        self.mock = MagicMock()
    
    def append(self, child):
        self.children.append(child)
    
    def pack_start(self, child, *args, **kwargs):
        self.children.append(child)
    
    def show_all(self):
        self.visible = True
        for child in self.children:
            if hasattr(child, 'show_all'):
                child.show_all()
    
    def __getattr__(self, name):
        return getattr(self.mock, name)

class MockButton(Gtk.Button):
    """Mock Gtk.Button that satisfies type checking."""
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._active = True
        self.visible = False
        self.mock = MagicMock()
    
    def get_active(self):
        return self._active
    
    def set_active(self, value):
        self._active = value
    
    def show_all(self):
        self.visible = True
    
    def __getattr__(self, name):
        return getattr(self.mock, name)

class MockToggleButton(Gtk.ToggleButton):
    """Mock Gtk.ToggleButton that satisfies type checking."""
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._active = True
        self.visible = False
        self.mock = MagicMock()
        if 'label' in kwargs:
            self.set_label(kwargs['label'])
    
    def get_active(self):
        return self._active
    
    def set_active(self, value):
        self._active = value
    
    def show_all(self):
        self.visible = True
    
    def __getattr__(self, name):
        return getattr(self.mock, name)

class MockComboBox(Gtk.ComboBox):
    """Mock Gtk.ComboBox that satisfies type checking."""
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._active = 0
        self.visible = False
        self.model = None
        self.mock = MagicMock()
    
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
    
    def __getattr__(self, name):
        return getattr(self.mock, name)

class MockDrawingArea(Gtk.DrawingArea):
    """Mock Gtk.DrawingArea that satisfies type checking."""
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.visible = False
        self.mock = MagicMock()
    
    def set_size_request(self, width, height):
        pass
    
    def set_vexpand(self, expand):
        pass
    
    def set_hexpand(self, expand):
        pass
    
    def get_vexpand(self):
        return True
    
    def get_hexpand(self):
        return True
    
    def __getattr__(self, name):
        return getattr(self.mock, name)

@pytest.fixture(autouse=True)
def gtk_version():
    """Ensure consistent GTK version across tests."""
    return '3.0'

@pytest.fixture
def mock_app():
    """Create a real GTK application for testing."""
    app = Gtk.Application.new('com.test.thermal2pro', Gio.ApplicationFlags.FLAGS_NONE)
    app.register()
    yield app
    app.quit()

@pytest.fixture(autouse=True)
def gtk_main_loop():
    """Set up and tear down GTK main loop for tests."""
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)
    yield
    while context.pending():
        context.iteration(False)

@pytest.fixture(autouse=True)
def cleanup_gtk():
    """Clean up GTK resources after each test."""
    yield
    for window in Gtk.Window.list_toplevels():
        window.destroy()

@pytest.fixture(autouse=True)
def mock_gtk_widgets():
    """Mock GTK widgets with type-safe versions."""
    patches = {
        'Box': MockBox,
        'Button': MockButton,
        'ToggleButton': MockToggleButton,
        'ComboBox': MockComboBox,
        'DrawingArea': MockDrawingArea,
    }
    
    with patch.multiple('gi.repository.Gtk', **patches):
        yield
