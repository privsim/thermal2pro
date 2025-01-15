import pytest
import os
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta
import time
from unittest.mock import mock_open, patch
from thermal2pro.storage.handler import StorageHandler

@pytest.fixture
def temp_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def storage_handler(temp_storage):
    handler = StorageHandler(max_age_days=7, min_free_space_gb=1)
    # Override storage paths for testing
    handler.primary_storage = str(temp_storage / "thermal_captures")
    handler.fallback_storage = str(temp_storage / "fallback_captures")
    handler._ensure_storage_paths()
    return handler

def create_test_capture(storage_path: Path, days_old: int) -> Path:
    """Helper to create a test capture file with a specific age."""
    timestamp = datetime.now() - timedelta(days=days_old)
    filename = f"thermal_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
    file_path = storage_path / filename
    # Create a 1MB test file
    with open(file_path, 'wb') as f:
        f.write(b'0' * 1024 * 1024)
    return file_path

def test_storage_paths(storage_handler):
    """Test storage path creation and validation."""
    # Both primary (USB) and fallback paths should exist
    assert Path(storage_handler.primary_storage).exists()
    assert Path(storage_handler.fallback_storage).exists()
    
    # Both should be directories
    assert Path(storage_handler.primary_storage).is_dir()
    assert Path(storage_handler.fallback_storage).is_dir()

def test_storage_monitoring_with_cleanup(storage_handler):
    """Test storage monitoring with cleanup triggers."""
    storage_path = Path(storage_handler.get_storage_path())
    
    # Create test files that will trigger cleanup
    for days in [5, 15, 25, 35]:  # Mix of old and new files
        create_test_capture(storage_path, days)
    
    # Monitor should detect cleanup needed
    status = storage_handler.monitor_storage()
    assert status["status"] == "ok"
    assert "cleanup_result" in status
    assert status["cleanup_result"]["deleted"] > 0  # Should have cleaned up old files
    
    # Verify only recent files remain
    remaining = storage_handler.list_captures()
    assert all(capture["age_days"] <= storage_handler.max_age_days for capture in remaining)

def test_storage_fallback(storage_handler, monkeypatch):
    """Test storage fallback behavior when USB is unavailable."""
    # Mock USB mount check to return False
    monkeypatch.setattr(storage_handler, '_is_usb_mounted', lambda: False)
    
    # Should fall back to fallback storage
    assert storage_handler.get_storage_path() == storage_handler.fallback_storage
    
    # Get storage info should indicate SD card
    info = storage_handler.get_storage_info()
    assert info is not None
    assert not info["is_external"]
    assert info["storage_type"] == "SD Card"

def test_usb_storage_detection(storage_handler, monkeypatch):
    """Test USB storage detection and usage."""
    # Create mock /proc/mounts content
    mock_mounts = "/dev/sda1 /media/usb0 ext4 rw 0 0\n"
    
    # Mock file operations
    monkeypatch.setattr(os.path, 'ismount', lambda x: x == "/media/usb0")
    monkeypatch.setattr('builtins.open', mock_open(read_data=mock_mounts))
    
    # USB should be detected
    assert storage_handler._is_usb_mounted()
    assert storage_handler.get_storage_path() == storage_handler.primary_storage
    
    # Storage info should indicate USB
    info = storage_handler.get_storage_info()
    assert info is not None
    assert info["is_external"]
    assert info["storage_type"] == "USB3"

def test_list_captures(storage_handler):
    # Create test captures with different ages
    storage_path = Path(storage_handler.get_storage_path())
    files = [
        create_test_capture(storage_path, 0),  # Today
        create_test_capture(storage_path, 5),  # 5 days old
        create_test_capture(storage_path, 10)  # 10 days old
    ]
    
    captures = storage_handler.list_captures()
    assert len(captures) == 3
    assert all("timestamp" in c and "age_days" in c for c in captures)
    # Verify sorting (newest first)
    assert captures[0]["age_days"] < captures[-1]["age_days"]

def test_cleanup_old_captures(storage_handler):
    storage_path = Path(storage_handler.get_storage_path())
    # Create some old and new captures
    old_file = create_test_capture(storage_path, 10)  # Should be deleted
    new_file = create_test_capture(storage_path, 2)   # Should be kept
    
    result = storage_handler.cleanup_old_captures()
    assert result["deleted"] == 1
    assert result["freed_space"] > 0
    assert not old_file.exists()
    assert new_file.exists()

def test_monitor_storage(storage_handler):
    storage_path = Path(storage_handler.get_storage_path())
    # Create some test captures
    for days in [1, 5, 9]:
        create_test_capture(storage_path, days)
    
    status = storage_handler.monitor_storage()
    assert status["status"] == "ok"
    assert "storage_info" in status
    assert "captures" in status
    assert status["captures"] == 3
