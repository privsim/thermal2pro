"""Tests for camera functionality."""
import numpy as np
import cv2
from thermal2pro.camera.mock_camera import MockThermalCamera

def test_frame_conversion():
    """Test frame color space conversions."""
    # Create grayscale test frame
    test_frame = np.zeros((192, 256), dtype=np.uint8)
    test_frame[50:150, 50:150] = 255  # Add white square
    
    # Convert to BGR
    bgr = cv2.cvtColor(test_frame, cv2.COLOR_GRAY2BGR)
    assert bgr.shape == (192, 256, 3)
    assert np.all(bgr[50:150, 50:150] == [255, 255, 255])

def test_mock_camera():
    """Test mock camera functionality."""
    cap = MockThermalCamera()
    ret, frame = cap.read()
    
    assert ret
    assert frame.shape == (192, 256, 3)  # BGR format
    assert frame.dtype == np.uint8
    
    # Test cleanup
    cap.release()
    assert not cap.isOpened()
