import numpy as np
import cv2
import time
from threading import Lock
from typing import Tuple, Optional

class MockThermalCamera:
    """Mock thermal camera for testing and development."""
    
    def __init__(self, width: int = 256, height: int = 192):
        self.width = width
        self.height = height
        self.is_open = True
        self._lock = Lock()
        self._frame_count = 0
        self._last_frame_time = time.time()
        
        # Create test pattern
        x = np.linspace(0, 255, width)
        y = np.linspace(0, 255, height)
        self.xx, self.yy = np.meshgrid(x, y)
        
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Simulate reading a frame from the camera.
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_open:
            return False, None
            
        with self._lock:
            # Create animated test pattern
            t = time.time()
            phase = (t * 2) % (2 * np.pi)
            
            # Generate simulated thermal pattern
            pattern = (
                np.sin(self.xx / 32 + phase) * 128 + 
                np.cos(self.yy / 32 - phase) * 128
            ).astype(np.uint8)
            
            # Add some noise
            noise = np.random.normal(0, 5, pattern.shape).astype(np.uint8)
            pattern = cv2.add(pattern, noise)
            
            # Create BGR frame
            frame = cv2.cvtColor(pattern, cv2.COLOR_GRAY2BGR)
            
            # Add simulated hot spots
            hot_spots = [
                (int(self.width/2 + np.sin(t) * 50), 
                 int(self.height/2 + np.cos(t) * 30))
            ]
            for x, y in hot_spots:
                cv2.circle(frame, (x, y), 10, (0, 0, 255), -1)
            
            # Simulate frame timing
            current_time = time.time()
            elapsed = current_time - self._last_frame_time
            if elapsed < 1/30:  # Cap at 30 FPS
                time.sleep(1/30 - elapsed)
            self._last_frame_time = time.time()
            
            self._frame_count += 1
            return True, frame
            
    def release(self):
        """Release the mock camera."""
        self.is_open = False
        
    def isOpened(self) -> bool:
        """Check if camera is open.
        
        Returns:
            True if camera is open
        """
        return self.is_open
        
    def set(self, prop_id: int, value: float) -> bool:
        """Set a camera property.
        
        Args:
            prop_id: Property identifier
            value: Property value
            
        Returns:
            True if successful
        """
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            self.width = int(value)
            return True
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            self.height = int(value)
            return True
        elif prop_id == cv2.CAP_PROP_FPS:
            # Simulate FPS setting
            return True
        elif prop_id == cv2.CAP_PROP_BUFFERSIZE:
            # Simulate buffer size setting
            return True
        return False
        
    def get(self, prop_id: int) -> float:
        """Get a camera property.
        
        Args:
            prop_id: Property identifier
            
        Returns:
            Property value
        """
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            return float(self.width)
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return float(self.height)
        elif prop_id == cv2.CAP_PROP_FPS:
            return 30.0
        elif prop_id == cv2.CAP_PROP_BUFFERSIZE:
            return 1.0
        return 0.0