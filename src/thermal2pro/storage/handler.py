import os
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class StorageHandler:
    """Handles storage management for thermal captures including cleanup and monitoring."""
    
    def __init__(self, max_age_days: int = 30, min_free_space_gb: int = 10):
        self.primary_storage = "/media/usb0/thermal_captures"
        self.fallback_storage = "/home/pi/thermal_captures"
        self.max_age_days = max_age_days
        self.min_free_space_gb = min_free_space_gb
        self._ensure_storage_paths()
        
    def _is_usb_mounted(self) -> bool:
        """Check if the USB drive is properly mounted."""
        try:
            if not os.path.ismount("/media/usb0"):
                return False
            
            with open("/proc/mounts", "r") as f:
                mounts = f.read()
                return "/dev/sda1" in mounts and "/media/usb0" in mounts
        except Exception as e:
            logger.error(f"Error checking USB mount: {e}")
            return False
    
    def _ensure_storage_paths(self):
        """Create storage directories if they don't exist."""
        paths_created = False
        try:
            Path(self.primary_storage).mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured primary storage at {self.primary_storage}")
            paths_created = True
        except Exception as e:
            logger.error(f"Failed to create primary storage: {e}")
            
        try:
            Path(self.fallback_storage).mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured fallback storage at {self.fallback_storage}")
            paths_created = True
        except Exception as e:
            logger.error(f"Failed to create fallback storage: {e}")
            
        # If neither path could be created, create a temporary test directory
        if not paths_created:
            import tempfile
            temp_dir = tempfile.mkdtemp()
            self.fallback_storage = str(Path(temp_dir) / "fallback_captures")
            Path(self.fallback_storage).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created temporary storage at {self.fallback_storage}")
        
    def get_storage_path(self) -> str:
        """Get the current storage path, preferring USB storage when available."""
        if self._is_usb_mounted() and os.access(self.primary_storage, os.W_OK):
            logger.info("Using USB storage for captures")
            return self.primary_storage
            
        logger.warning("USB storage unavailable, falling back to SD card storage")
        return self.fallback_storage
        
    def get_capture_path(self, prefix="thermal"):
        storage = self.get_storage_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(Path(storage) / f"{prefix}_{timestamp}.jpg")
        
    def get_storage_info(self) -> Optional[Dict[str, any]]:
        """Get information about the current storage location."""
        storage = self.get_storage_path()
        try:
            total, used, free = shutil.disk_usage(storage)
            is_external = self._is_usb_mounted() and storage == self.primary_storage
            
            info = {
                "path": storage,
                "total_gb": total // (2**30),
                "used_gb": used // (2**30),
                "free_gb": free // (2**30),
                "is_external": is_external,
                "storage_type": "USB3" if is_external else "SD Card"
            }
            
            logger.info(f"Storage info: {info}")
            return info
            
        except OSError as e:
            logger.error(f"Failed to get storage info for {storage}: {e}")
            return None
            
    def list_captures(self) -> List[Dict[str, str]]:
        """List all captures with their timestamps and paths."""
        storage = self.get_storage_path()
        captures = []
        now = datetime.now()
        try:
            for file in Path(storage).glob("thermal_*.jpg"):
                timestamp_str = file.stem.split("_", 1)[1]  # Remove 'thermal_' prefix
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    age_days = (now - timestamp).days
                    captures.append({
                        "path": str(file),
                        "timestamp": timestamp.isoformat(),
                        "age_days": age_days
                    })
                except ValueError:
                    continue
        except OSError:
            return []
            
        return sorted(captures, key=lambda x: x["timestamp"], reverse=True)
    
    def cleanup_old_captures(self, force: bool = False) -> Dict[str, int]:
        """Clean up old captures based on age and space constraints.
        
        Args:
            force: If True, clean up all files older than max_age_days regardless of space
        """
        result = {"deleted": 0, "freed_space": 0}
        storage = self.get_storage_path()
        
        # Check if cleanup is needed
        storage_info = self.get_storage_info()
        if not storage_info:
            return result
        
        need_space = storage_info["free_gb"] < self.min_free_space_gb
        
        captures = self.list_captures()
        old_captures = [c for c in captures if c["age_days"] > self.max_age_days]
        
        if old_captures or need_space or force:
            for capture in old_captures:
                try:
                    file_path = Path(capture["path"])
                    if file_path.exists():
                        size = file_path.stat().st_size
                        file_path.unlink()
                        result["deleted"] += 1
                        result["freed_space"] += size // (2**20)  # Convert to MB
                except OSError as e:
                    logger.error(f"Error cleaning up file {capture['path']}: {e}")
                    continue
            
            # If we still need space, clean up older files
            if need_space:
                remaining = self.list_captures()
                for capture in remaining:
                    try:
                        file_path = Path(capture["path"])
                        if file_path.exists():
                            size = file_path.stat().st_size
                            file_path.unlink()
                            result["deleted"] += 1
                            result["freed_space"] += size // (2**20)
                            
                            # Check if we've freed enough space
                            current_info = self.get_storage_info()
                            if current_info and current_info["free_gb"] >= self.min_free_space_gb:
                                break
                    except OSError:
                        continue
        
        return result
    
    def monitor_storage(self) -> Dict[str, any]:
        """Monitor storage status and trigger cleanup if needed."""
        storage_info = self.get_storage_info()
        if not storage_info:
            return {"status": "error", "message": "Storage not accessible"}
        
        cleanup_needed = storage_info["free_gb"] < self.min_free_space_gb
        captures = self.list_captures()
        old_captures = [c for c in captures if c["age_days"] > self.max_age_days]
        
        # Run cleanup if needed
        cleanup_result = self.cleanup_old_captures(force=bool(old_captures) or cleanup_needed)
        
        status = {
            "status": "ok",
            "storage_info": storage_info,
            "captures": len(captures),
            "cleanup_needed": cleanup_needed,
            "cleanup_result": cleanup_result
        }
        
        return status