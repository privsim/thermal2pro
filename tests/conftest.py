"""Test configuration and fixtures."""
import os
import gi

# Use GTK 4.0
os.environ['GTK_VERSION'] = '4.0'
gi.require_version('Gtk', '4.0')

import pytest
from gi.repository import Gtk, GLib, Gdk, Gio
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def gtk_version():
    """Ensure consistent GTK version across tests."""
    return '4.0'

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

@pytest.fixture
def mock_window():
    """Create a mock window."""
    window = MagicMock()
    window.controls_container = Gtk.Box()
    window.controls_container.pack_start = MagicMock()
    window.controls_container.remove = MagicMock()
    window.controls_container.show = MagicMock()
    return window
