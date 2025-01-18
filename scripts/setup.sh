#!/usr/bin/env bash
set -euo pipefail

BASE_DIR=$(pwd)
SRC_DIR="${BASE_DIR}/src/thermal2pro"
VENV_DIR="${BASE_DIR}/thermalenv"

install_system_dependencies() {
    echo "Installing system dependencies..."
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y \
            python3-gi \
            python3-gi-cairo \
            gir1.2-gtk-4.0 \
            libgirepository1.0-dev \
            gcc \
            libcairo2-dev \
            pkg-config \
            python3-dev
    else
        echo "Warning: apt not found. Please install required dependencies manually:"
        echo "- python3-gi"
        echo "- python3-gi-cairo"
        echo "- gir1.2-gtk-4.0"
        echo "- libgirepository1.0-dev"
        echo "- gcc"
        echo "- libcairo2-dev"
        echo "- pkg-config"
        echo "- python3-dev"
    fi
}

setup_user_permissions() {
    echo "Setting up user permissions..."
    if getent group video > /dev/null; then
        if ! groups | grep -q "\bvideo\b"; then
            sudo usermod -a -G video "$USER"
            echo "Added user to video group. Please log out and back in for changes to take effect."
        else
            echo "User already in video group."
        fi
    else
        echo "Warning: video group not found. Please ensure proper camera permissions manually."
    fi
}

create_directory_structure() {
    echo "Creating directory structure..."
    mkdir -p "${SRC_DIR}"/{camera,storage,ui}
    mkdir -p "${BASE_DIR}"/{tests,scripts,docs/img}

    touch "${SRC_DIR}"/__init__.py
    touch "${SRC_DIR}"/camera/__init__.py
    touch "${SRC_DIR}"/storage/__init__.py
    touch "${SRC_DIR}"/ui/__init__.py
    touch "${BASE_DIR}"/tests/__init__.py
}

setup_virtual_environment() {
    echo "Setting up Python virtual environment..."
    
    # Check if venv exists and is valid
    if [ ! -d "$VENV_DIR" ] || [ ! -f "${VENV_DIR}/bin/activate" ]; then
        echo "Creating new virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Source the virtual environment
    # shellcheck disable=SC1090
    source "${VENV_DIR}/bin/activate"
    
    # Verify activation
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        echo "Error: Virtual environment activation failed"
        exit 1
    fi
    
    echo "Upgrading pip and installing dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    
    # Install in development mode
    python3 -m pip install -e .
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
3. Log out and back in for group permissions to take effect
4. Activate the virtual environment: `source thermalenv/bin/activate`
5. Run the application: `python -m thermal2pro.main`

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
3. Log out and back in for group permissions to take effect
4. Activate the virtual environment: `source thermalenv/bin/activate`
5. Run: `python -m thermal2pro.main`

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

# Install system dependencies first
install_system_dependencies

# Set up directory structure
create_directory_structure

# Set up Python environment
setup_virtual_environment

# Migrate any existing files
migrate_existing_files

# Create configuration files
create_config_files

# Set up user permissions last
setup_user_permissions

echo "Setup complete!"
echo "Please log out and back in for group permissions to take effect."
echo "Then activate your virtual environment with:"
echo "source thermalenv/bin/activate"
