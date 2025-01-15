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
