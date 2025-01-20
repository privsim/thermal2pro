#!/usr/bin/env bash
set -euo pipefail

echo "Setting up test environment..."

# Ensure we are in the virtual environment
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo "Virtual environment not active! Please activate it first."
    exit 1
fi

# Install development dependencies
echo "Installing test dependencies..."
pip install -r requirements.txt

# Install package in editable mode
echo "Installing thermal2pro in editable mode..."
pip install -e .

# Run a test to verify setup
echo "Running test verification..."
python -m pytest tests/test_ui.py -v

echo "Test environment setup complete!"