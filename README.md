# Thermal2Pro Camera

Thermal imaging application for P2 Pro camera.

## Installation

1. Clone this repository
2. Run `./scripts/setup.sh` to set up the project
3. Activate the virtual environment: `source thermalenv/bin/activate`
4. Run the application: `python -m thermal2pro.main`

## Development

### Running Tests

Tests can be run in two modes:

1. Normal mode (with GUI):
```bash
pytest tests/ -v
```

2. Headless mode (for CI/CD):
```bash
# Install Xvfb
sudo apt install xvfb  # On Ubuntu/Debian

# Run tests headless
CI=1 pytest tests/ -v
# or
pytest tests/ -v --headless
```

### System Requirements

- Python 3.9 or newer
- GTK 4.0
- OpenCV
- For development: Xvfb (for headless testing)

### Dependencies

```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 libgirepository1.0-dev

# Fedora
sudo dnf install python3-gobject gtk4-devel

# Arch
sudo pacman -S python-gobject gtk4

# macOS
brew install gtk4 gobject-introspection pygobject3
```

## CI/CD

The project uses GitHub Actions for continuous integration. Tests are run automatically on:
- Every push to main
- Every pull request

Tests in CI run in headless mode using Xvfb.

## License

MIT License