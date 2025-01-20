"""Test configuration and fixtures."""
import os
import pytest
import gi

# Use GTK 4.0
os.environ['GTK_VERSION'] = '4.0'
gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, GLib, Gdk, Gio

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "gtk: mark test as requiring GTK (UI/display test)"
    )

@pytest.fixture(scope='session', autouse=True)
def gtk_settings():
    """Configure GTK settings for tests."""
    settings = Gtk.Settings.get_default()
    if settings:
        # Disable animations and transitions for testing
        settings.set_property("gtk-enable-animations", False)

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
def mock_app():
    """Create a real GTK application for testing."""
    app = Gtk.Application.new('com.test.thermal2pro', Gio.ApplicationFlags.FLAGS_NONE)
    app.register()
    yield app
    app.quit()
