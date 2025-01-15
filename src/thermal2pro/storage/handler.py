import os
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class StorageHandler:
    """Handles storage management for thermal captures including cleanup and monitoring.
    
    Storage Hierarchy:
    - Primary: USB3 drive mounted at /dev/sda1 (configured in fstab)
    - Fallback: SD card storage (limited space, used only when USB unavailable)
    
    The system is designed to primarily use the USB3 drive for storage due to
    the limited space on the Raspberry Pi's SD card. The fallback storage should
    only be used temporarily when the USB drive is unavailable.
    """
    
    def __init__(self, max_age_days: int = 30, min_free_space_gb: int = 10):
        # Primary storage on USB3 drive mounted from /dev/sda1
        self.primary_storage = "/media/usb0/thermal_captures"
        # Fallback to SD card only when necessary
        self.fallback_storage = "/home/pi/thermal_captures"
        self.max_age_days = max_age_days
        self.min_free_space_gb = min_free_space_gb
        self._ensure_storage_paths()
        
    def _is_usb_mounted(self) -> bool:
        """Check if the USB drive is properly mounted."""
        try:
            # Check if mount point exists and is mounted
            if not os.path.ismount("/media/usb0"):
                return False
            
            # Verify it's the correct device by checking mount point
            with open("/proc/mounts", "r") as f:
                mounts = f.read()
                return "/dev/sda1" in mounts and "/media/usb0" in mounts
        except Exception as e:
            logger.error(f"Error checking USB mount: {e}")
            return False
    
    def _ensure_storage_paths(self):
        """Create storage directories if they don't exist."""
        try:
            Path(self.primary_storage).mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured primary storage at {self.primary_storage}")
        except Exception as e:
            logger.error(f"Failed to create primary storage: {e}")
            
        try:
            Path(self.fallback_storage).mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured fallback storage at {self.fallback_storage}")
        except Exception as e:
            logger.error(f"Failed to create fallback storage: {e}")
        
    def get_storage_path(self) -> str:
        """Get the current storage path, preferring USB storage when available.
        
        Returns:
            str: Path to the current storage location
        """
        if self._is_usb_mounted() and os.access(self.primary_storage, os.W_OK):
            logger.info("Using USB storage for captures")
            return self.primary_storage
            
        logger.warning("USB storage unavailable, falling back to SD card storage")
        if not os.access(self.fallback_storage, os.W_OK):
            logger.error("Neither USB nor fallback storage is writable!")
            
        return self.fallback_storage
        
    def get_capture_path(self, prefix="thermal"):
        storage = self.get_storage_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(Path(storage) / f"{prefix}_{timestamp}.jpg")
        
    def get_storage_info(self) -> Optional[Dict[str, any]]:
        """Get information about the current storage location.
        
        Returns:
            Optional[Dict[str, any]]: Storage information including space usage and type,
                                    or None if storage is not accessible
        """
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
        try:
            for file in Path(storage).glob("thermal_*.jpg"):
                timestamp_str = file.stem.split("_", 1)[1]  # Remove 'thermal_' prefix
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    captures.append({
                        "path": str(file),
                        "timestamp": timestamp.isoformat(),
                        "age_days": (datetime.now() - timestamp).days
                    })
                except ValueError:
                    continue  # Skip files that don't match expected format
        except OSError:
            return []
        return sorted(captures, key=lambda x: x["timestamp"], reverse=True)
    
    def cleanup_old_captures(self) -> Dict[str, int]:
        """Clean up old captures based on age and space constraints."""
        result = {"deleted": 0, "freed_space": 0}
        storage = self.get_storage_path()
        
        # Check if cleanup is needed
        storage_info = self.get_storage_info()
        if not storage_info or storage_info["free_gb"] >= self.min_free_space_gb:
            return result
            
        captures = self.list_captures()
        for capture in captures:
            try:
                # Remove files older than max_age_days
                if capture["age_days"] > self.max_age_days:
                    file_path = Path(capture["path"])
                    if file_path.exists():
                        size = file_path.stat().st_size
                        file_path.unlink()
                        result["deleted"] += 1
                        result["freed_space"] += size // (2**20)  # Convert to MB
                        
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
            
        status = {
            "status": "ok",
            "storage_info": storage_info,
            "captures": len(self.list_captures()),
            "cleanup_needed": storage_info["free_gb"] < self.min_free_space_gb
        }
        
        if status["cleanup_needed"]:
            cleanup_result = self.cleanup_old_captures()
            status["cleanup_result"] = cleanup_result
            
        return status
