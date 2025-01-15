#!/usr/bin/env bash
set -euo pipefail

BASE_DIR=$(pwd)
SRC_DIR="${BASE_DIR}/src/thermal2pro"
VENV_DIR="${BASE_DIR}/thermalenv"

create_directory_structure() {
    mkdir -p "${SRC_DIR}"/{camera,storage,ui}
    mkdir -p "${BASE_DIR}"/{tests,scripts,docs/img}

    touch "${SRC_DIR}"/__init__.py
    touch "${SRC_DIR}"/camera/__init__.py
    touch "${SRC_DIR}"/storage/__init__.py
    touch "${SRC_DIR}"/ui/__init__.py
    touch "${BASE_DIR}"/tests/__init__.py
}

setup_virtual_environment() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip
    pip install pytest PyGObject
    pip install -r requirements.txt
}

migrate_existing_files() {
    if [ -f "${BASE_DIR}/thermal_camera.py" ]; then
        echo "Migrating existing thermal_camera.py..."
        
        # Extract camera-related code
        awk '/class ThermalWindow/,/class ThermalApp/' thermal_camera.py > "${SRC_DIR}/ui/window.py"
        
        # Create main.py
        cat > "${SRC_DIR}/main.py" << 'EOL'
#!/usr/bin/env python3
import gi
try:
    gi.require_version('Gtk', '4.0')
except ValueError:
    gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from thermal2pro.ui.window import ThermalWindow

class ThermalApp(Gtk.Application):
    def __init__(self):
        super().__init__()

    def do_activate(self):
        win = ThermalWindow(self)
        win.present()

def main():
    app = ThermalApp()
    return app.run(None)

if __name__ == "__main__":
    main()
EOL
        chmod +x "${SRC_DIR}/main.py"
        
        # Create storage handler
        if [ -f "${BASE_DIR}/storage_handler.py" ]; then
            cp "${BASE_DIR}/storage_handler.py" "${SRC_DIR}/storage/handler.py"
        fi
    fi
}

create_config_files() {
    # Create pyproject.toml
    cat > "${BASE_DIR}/pyproject.toml" << 'EOL'
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "thermal2pro"
version = "0.1.0"
description = "Thermal imaging application for P2 Pro camera"
requires-python = ">=3.9"
dependencies = [
    "numpy>=1.26.0",
    "opencv-python-headless>=4.8.0",
    "Pillow>=10.0.0",
    "pycairo>=1.24.0",
    "PyGObject>=3.42.0",
]

[project.scripts]
thermal2pro = "thermal2pro.main:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"

[tool.setuptools]
package-dir = {"" = "src"}
EOL

    # Create systemd service file
    cat > "${BASE_DIR}/scripts/thermal2pro.service" << 'EOL'
[Unit]
Description=Thermal2Pro Camera Service
After=network.target

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
Environment=GTK_A11Y=none
WorkingDirectory=/home/pi/2pro
ExecStart=/home/pi/2pro/thermalenv/bin/python -m thermal2pro.main
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

    # Create basic README
    cat > "${BASE_DIR}/README.md" << 'EOL'
# Thermal2Pro Camera

Thermal imaging application for P2 Pro camera.

## Installation

1. Clone this repository
2. Run `./scripts/setup.sh` to set up the project
3. Activate the virtual environment: `source thermalenv/bin/activate`
4. Run the application: `python -m thermal2pro.main`

## Development

- Use `pytest` to run tests
- See `docs/` for detailed documentation

## License

MIT License
EOL

    # Create installation documentation
    cat > "${BASE_DIR}/docs/INSTALL.md" << 'EOL'
# Installation Guide

## System Requirements

- Raspberry Pi (tested on Pi 4)
- P2 Pro thermal camera
- Python 3.9 or newer

## System Dependencies

```bash
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 \
    libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev
```

## Project Setup

1. Clone the repository
2. Run `./scripts/setup.sh`
3. Add your user to the video group: `sudo usermod -a -G video $USER`
4. Log out and back in for group changes to take effect

## Running the Application

1. Activate the virtual environment: `source thermalenv/bin/activate`
2. Run: `python -m thermal2pro.main`

## Systemd Service Installation

To run on startup:

```bash
sudo cp scripts/thermal2pro.service /etc/systemd/system/
sudo systemctl enable thermal2pro
sudo systemctl start thermal2pro
```
EOL
}

# Main execution
echo "Setting up Thermal2Pro project..."
create_directory_structure
setup_virtual_environment
migrate_existing_files
create_config_files

echo "Installing the package in development mode..."
pip install -e .

echo "Setup complete! Activate your virtual environment with:"
echo "source thermalenv/bin/activate"
