import os
import shutil
from datetime import datetime
from pathlib import Path

class StorageHandler:
    def __init__(self):
        self.primary_storage = "/mnt/thermal_storage/thermal_captures"
        self.fallback_storage = str(Path.home() / "thermal_captures")
        self._ensure_storage_paths()
        
    def _ensure_storage_paths(self):
        Path(self.primary_storage).mkdir(parents=True, exist_ok=True)
        Path(self.fallback_storage).mkdir(parents=True, exist_ok=True)
        
    def get_storage_path(self):
        if os.access(self.primary_storage, os.W_OK):
            return self.primary_storage
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
        except OSError:
            return None
