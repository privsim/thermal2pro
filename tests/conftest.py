"""Test configuration and fixtures."""
import os
import gi
import pytest
import platform
import sys
from pathlib import Path

# Use GTK 4.0 exclusively
gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, GLib, Gdk, Gio
from unittest.mock import MagicMock, patch

def pytest_addoption(parser):
    """Add CLI options for test configuration."""
    parser.addoption(
        "--headless",
        action="store_true",
        default=bool(os.environ.get('CI')),
        help="run in headless mode"
    )

@pytest.fixture(scope="session", autouse=True)
def gtk_init(pytestconfig):
    """Initialize GTK before running tests."""
    if platform.system() == "Darwin":
        # On macOS, we'll use a null display
        os.environ["GDK_BACKEND"] = "x11"
        os.environ["DISPLAY"] = ":0"
    elif platform.system() == "Linux" and pytestconfig.getoption("--headless"):
        # On Linux with headless mode
        try:
            import subprocess
            display_num = "99"
            os.environ["DISPLAY"] = f":{display_num}"
            process = subprocess.Popen(
                ["Xvfb", f":{display_num}", "-screen", "0", "1280x1024x24"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            yield process
            process.terminate()
            process.wait(timeout=5)
            return
        except FileNotFoundError:
            pytest.skip("Xvfb not installed. Install with: sudo apt install xvfb")
    
    # For all other cases, initialize GTK normally
    app = Gtk.Application(application_id="com.test.thermal2pro")
    app.register()
    yield app
    app.quit()

@pytest.fixture(autouse=True)
def skip_gtk_tests(request):
    """Skip GTK-dependent tests in certain environments."""
    if pytest.mark.gtk in request.node.iter_markers():
        if platform.system() == "Darwin" and not os.environ.get("DISPLAY"):
            pytest.skip("GTK tests require X11 on macOS")

@pytest.fixture
def mock_app():
    """Create a GTK application for testing."""
    app = Gtk.Application(application_id="com.test.thermal2pro")
    app.register()
    yield app
    app.quit()

@pytest.fixture(autouse=True)
def gtk_main_loop():
    """Set up and tear down GTK main loop for tests."""
    loop = GLib.MainLoop()
    context = GLib.MainContext.default()
    
    while context.pending():
        context.iteration(False)
    
    yield loop
    
    while context.pending():
        context.iteration(False)

@pytest.fixture
def test_widget_container():
    """Create a container for testing widgets."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.set_margin_start(5)
    box.set_margin_end(5)
    box.set_margin_top(5)
    box.set_margin_bottom(5)
    return box

@pytest.fixture
def drawing_area():
    """Create a DrawingArea for testing."""
    area = Gtk.DrawingArea()
    area.set_size_request(256, 192)
    area.set_vexpand(True)
    area.set_hexpand(True)
    return area

@pytest.fixture
def test_frame():
    """Create a test frame for camera tests."""
    import numpy as np
    frame = np.zeros((192, 256, 3), dtype=np.uint8)
    frame[50:150, 50:150] = 255  # Add white square
    return frame

@pytest.fixture
def mock_camera():
    """Create a mock camera for testing."""
    from thermal2pro.camera.mock_camera import MockThermalCamera
    return MockThermalCamera