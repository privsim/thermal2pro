import os
import shutil
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageHandler:
    def __init__(self):
        self.primary_storage = "/mnt/thermal_storage/thermal_captures"
        self.fallback_storage = str(Path.home() / "thermal_captures")
        self._ensure_storage_paths()
        
    def _ensure_storage_paths(self):
        # Always ensure fallback exists
        Path(self.fallback_storage).mkdir(parents=True, exist_ok=True)
        
        # Try to create primary if possible
        try:
            primary_path = Path(self.primary_storage)
            if not primary_path.exists():
                primary_path.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = primary_path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            logger.warning(f"Primary storage unavailable: {e}")
        
    def get_storage_path(self):
        if os.access(self.primary_storage, os.W_OK):
            try:
                # Double check with actual write test
                test_file = Path(self.primary_storage) / ".write_test"
                test_file.touch()
                test_file.unlink()
                return self.primary_storage
            except Exception as e:
                logger.warning(f"Primary storage write test failed: {e}")
        return self.fallback_storage
        
    def get_capture_path(self, prefix="thermal"):
        storage = self.get_storage_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(Path(storage) / f"{prefix}_{timestamp}.jpg")
        
    def get_storage_info(self):
        storage = self.get_storage_path()
        try:
            total, used, free = shutil.disk_usage(storage)
            return {
                "path": storage,
                "total_gb": total // (2**30),
                "used_gb": used // (2**30),
                "free_gb": free // (2**30),
                "is_external": storage.startswith("/mnt/thermal_storage")
            }
        except OSError as e:
            logger.error(f"Error getting storage info: {e}")
            return None
