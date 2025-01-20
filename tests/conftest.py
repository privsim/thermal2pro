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
        # Disable native decorations to avoid window manager interference
        settings.set_property("gtk-application-prefer-dark-theme", True)
        # Ensure consistent font rendering
        settings.set_property("gtk-xft-antialias", 1)
        settings.set_property("gtk-xft-hinting", 1)

@pytest.fixture(autouse=True)
def gtk_main_loop():
    """Set up and tear down GTK main loop for tests."""
    context = GLib.MainContext.default()
    try:
        # Process any pending events before test
        while context.pending():
            context.iteration(False)
        yield
    finally:
        # Ensure event loop is flushed after test
        timeout = 0
        while context.pending() and timeout < 100:
            context.iteration(False)
            timeout += 1

@pytest.fixture(autouse=True)
def cleanup_gtk():
    """Clean up GTK resources after each test."""
    yield
    for window in Gtk.Window.list_toplevels():
        window.destroy()

@pytest.fixture
def mock_app(request):
    """Create a real GTK application for testing."""
    # Create unique application ID for each test
    app_id = f'com.test.thermal2pro.{request.node.name}'
    app = Gtk.Application.new(app_id, Gio.ApplicationFlags.FLAGS_NONE)
    
    try:
        app.register()
        yield app
    finally:
        # Ensure cleanup happens even if test fails
        try:
            app.quit()
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
        except Exception as e:
            print(f"Warning: Error during app cleanup: {e}")

