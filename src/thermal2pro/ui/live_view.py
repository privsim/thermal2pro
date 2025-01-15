import time
import numpy as np
from collections import deque
from typing import Optional, Deque, Tuple
import cv2
from dataclasses import dataclass
from threading import Lock

@dataclass
class FrameMetrics:
    fps: float
    frame_time: float
    dropped_frames: int
    buffer_usage: float

class LiveViewHandler:
    def __init__(self, buffer_size: int = 5):
        """Initialize live view handler with frame buffer.
        
        Args:
            buffer_size: Maximum number of frames to keep in buffer
        """
        self._frame_buffer: Deque[np.ndarray] = deque(maxlen=buffer_size)
        self._metrics = FrameMetrics(fps=0.0, frame_time=0.0, dropped_frames=0, buffer_usage=0.0)
        self._last_frame_time = time.time()
        self._fps_samples: Deque[float] = deque(maxlen=30)  # Rolling window for FPS calculation
        self._frame_lock = Lock()
        self._processing = False
        self._skip_next = False
        
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], FrameMetrics]:
        """Process a new frame and update metrics.
        
        Args:
            frame: Input frame to process
            
        Returns:
            Tuple of (processed frame, current metrics)
        """
        current_time = time.time()
        frame_time = current_time - self._last_frame_time
        self._last_frame_time = current_time
        
        # Update FPS calculation
        if frame_time > 0:
            self._fps_samples.append(1.0 / frame_time)
        
        # Check if we should skip this frame
        if self._should_skip_frame(frame_time):
            self._metrics.dropped_frames += 1
            return None, self._metrics
            
        with self._frame_lock:
            # Add frame to buffer
            self._frame_buffer.append(frame)
            
            # Update metrics
            self._metrics.fps = sum(self._fps_samples) / len(self._fps_samples) if self._fps_samples else 0
            self._metrics.frame_time = frame_time
            self._metrics.buffer_usage = len(self._frame_buffer) / self._frame_buffer.maxlen
            
            # Return most recent frame
            return frame, self._metrics
    
    def _should_skip_frame(self, frame_time: float) -> bool:
        """Determine if we should skip processing this frame.
        
        Args:
            frame_time: Time since last frame
            
        Returns:
            True if frame should be skipped
        """
        # Skip if we're falling behind (frame time > 2x target frame time)
        if frame_time > 0.080:  # More than 80ms (targeting ~30fps)
            return True
            
        # Skip if buffer is nearly full
        if len(self._frame_buffer) >= self._frame_buffer.maxlen * 0.9:
            return True
            
        # Skip every other frame if FPS is too high
        if self._metrics.fps > 35:
            self._skip_next = not self._skip_next
            return self._skip_next
            
        return False
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame from the buffer.
        
        Returns:
            Latest frame or None if buffer is empty
        """
        with self._frame_lock:
            return self._frame_buffer[-1] if self._frame_buffer else None
    
    def clear_buffer(self) -> None:
        """Clear the frame buffer and reset metrics."""
        with self._frame_lock:
            self._frame_buffer.clear()
            self._fps_samples.clear()
            self._metrics = FrameMetrics(
                fps=0.0,
                frame_time=0.0,
                dropped_frames=0,
                buffer_usage=0.0
            )
            self._last_frame_time = time.time()
            self._skip_next = False
    
    def get_metrics(self) -> FrameMetrics:
        """Get current performance metrics.
        
        Returns:
            Current FrameMetrics
        """
        with self._frame_lock:
            # Ensure buffer usage is accurate
            self._metrics.buffer_usage = len(self._frame_buffer) / self._frame_buffer.maxlen
            return self._metrics