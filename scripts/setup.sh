#!/usr/bin/env bash
set -euo pipefail

BASE_DIR=$(pwd)
VENV_DIR="${BASE_DIR}/thermalenv"

install_system_dependencies() {
    echo "Installing system dependencies..."
    if command -v apt &> /dev/null; then
        sudo apt update
        # Install GTK4 as required by project
        sudo apt install -y \
        python3-gi \
        python3-gi-cairo \
        gir1.2-gtk-4.0 \
        libgirepository1.0-dev \
        gcc \
        libcairo2-dev \
        pkg-config \
        python3-dev \
            libgtk-4-dev \
            xvfb
    else
        echo "Warning: apt not found. Please install required dependencies manually:"
        echo "- python3-gi"
        echo "- python3-gi-cairo"
        echo "- gir1.2-gtk-4.0"
        echo "- libgtk-4-dev"
        echo "- xvfb"
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

setup_virtual_environment() {
    echo "Setting up Python virtual environment..."
    
    # Check if venv exists and is valid
    if [ ! -d "$VENV_DIR" ] || [ ! -f "${VENV_DIR}/bin/activate" ]; then
        echo "Creating new virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Create activate.d directory if it doesn't exist
    mkdir -p "${VENV_DIR}/bin/activate.d"

    # Create environment setup file
    cat > "${VENV_DIR}/bin/activate.d/thermal2pro.sh" << 'EOL'
#!/bin/bash
# Disable GTK accessibility bus to prevent warnings
export GTK_A11Y=none
# Use GTK4 as required by project
export GTK_VERSION=4.0
EOL
    chmod +x "${VENV_DIR}/bin/activate.d/thermal2pro.sh"
    
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

# Main execution
echo "Setting up Thermal2Pro project..."

# Install system dependencies first
install_system_dependencies

# Set up Python environment
setup_virtual_environment

# Set up user permissions last
setup_user_permissions

echo "Setup complete!"
echo "Please log out and back in for group permissions to take effect."
echo "Then activate your virtual environment with:"
echo "source thermalenv/bin/activate"
