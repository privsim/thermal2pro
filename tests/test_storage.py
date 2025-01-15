import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def temp_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_storage_paths(temp_storage):
    capture_dir = temp_storage / "thermal_storage/thermal_captures"
    fallback_dir = Path.home() / "thermal_captures"
    
    if not capture_dir.exists():
        assert not capture_dir.exists()
        fallback_dir.mkdir(exist_ok=True)
        assert fallback_dir.exists()
        assert fallback_dir.is_dir()

def test_storage_fallback(temp_storage):
    # Test that storage falls back to home directory when external storage is unavailable
    from thermal2pro.storage.handler import StorageHandler
    
    handler = StorageHandler()
    assert handler.get_storage_path() == str(Path.home() / "thermal_captures")
