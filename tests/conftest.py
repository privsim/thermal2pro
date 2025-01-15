import pytest
import os
import numpy as np

# Disable GTK accessibility for testing
os.environ['GTK_A11Y'] = 'none'

@pytest.fixture
def mock_camera():
    class MockVideoCapture:
        def __init__(self, test_frame=None):
            self.test_frame = test_frame if test_frame is not None else np.zeros((192, 256), dtype=np.uint8)
            self.is_open = True
            
        def read(self):
            return True, self.test_frame
            
        def isOpened(self):
            return self.is_open
            
        def release(self):
            self.is_open = False
    
    return MockVideoCapture

@pytest.fixture
def test_frame():
    frame = np.zeros((192, 256), dtype=np.uint8)
    frame[96:146, 128:178] = 255  # Create a white rectangle in the middle
    return frame
