import pytest
import numpy as np
import cv2

def test_frame_conversion(test_frame):
    gray = cv2.cvtColor(test_frame, cv2.COLOR_GRAY2BGR)
    colored = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
    rgb = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    
    assert rgb.shape == (192, 256, 3)
    assert rgb.dtype == np.uint8
    assert np.any(rgb != 0)  # Check that coloring happened

def test_mock_camera(mock_camera):
    cap = mock_camera()
    assert cap.isOpened()
    
    ret, frame = cap.read()
    assert ret
    assert frame.shape == (192, 256)
    
    cap.release()
    assert not cap.is_open
