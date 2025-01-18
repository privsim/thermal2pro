import unittest
import gi
import tempfile
from pathlib import Path
import cv2
import numpy as np
from unittest.mock import patch, MagicMock
import time
import shutil

try:
    gi.require_version('Gtk', '4.0')
    GTK4 = True
    print("Using GTK 4.0")
except ValueError:
    gi.require_version('Gtk', '3.0')
    GTK4 = False
    print("Using GTK 3.0")
from gi.repository import Gtk, GLib

from thermal2pro.camera.mock_camera import MockThermalCamera

class TestMockCamera(unittest.TestCase):
    """Test mock camera functionality."""
    
    def setUp(self):
        """Set up test case."""
        print("\nSetting up mock camera test")
        self.camera = MockThermalCamera()
    
    def tearDown(self):
        """Clean up test case."""
        print("\nCleaning up mock camera test")
        if hasattr(self, 'camera'):
            self.camera.release()
    
    def test_initialization(self):
        """Test camera initialization."""
        print("\nTesting camera initialization")
        self.assertTrue(self.camera.isOpened())
        self.assertEqual(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH), 256)
        self.assertEqual(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT), 192)
        print("Camera initialization test passed")
    
    def test_frame_capture(self):
        """Test frame capture."""
        print("\nTesting frame capture")
        ret, frame = self.camera.read()
        self.assertTrue(ret)
        self.assertIsInstance(frame, np.ndarray)
        self.assertEqual(frame.shape, (192, 256, 3))
        print("Frame capture test passed")
    
    def test_frame_processing(self):
        """Test frame processing."""
        print("\nTesting frame processing")
        ret, frame = self.camera.read()
        self.assertTrue(ret)
        
        # Test grayscale conversion
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.assertEqual(gray.shape, (192, 256))
        
        # Test colormap application
        colored = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        self.assertEqual(colored.shape, (192, 256, 3))
        
        # Test RGB conversion
        rgb = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
        self.assertEqual(rgb.shape, (192, 256, 3))
        print("Frame processing test passed")
    
    def test_frame_saving(self):
        """Test frame saving."""
        print("\nTesting frame saving")
        with tempfile.TemporaryDirectory() as temp_dir:
            ret, frame = self.camera.read()
            self.assertTrue(ret)
            
            filepath = Path(temp_dir) / "test_frame.jpg"
            cv2.imwrite(str(filepath), frame)
            
            self.assertTrue(filepath.exists())
            saved_frame = cv2.imread(str(filepath))
            self.assertIsNotNone(saved_frame)
            self.assertEqual(saved_frame.shape, (192, 256, 3))
        print("Frame saving test passed")
    
    def test_cleanup(self):
        """Test cleanup."""
        print("\nTesting cleanup")
        self.assertTrue(self.camera.isOpened())
        self.camera.release()
        self.assertFalse(self.camera.isOpened())
        print("Cleanup test passed")

class TestImageProcessing(unittest.TestCase):
    """Test image processing functionality."""
    
    def setUp(self):
        """Set up test case."""
        print("\nSetting up image processing test")
        self.camera = MockThermalCamera()
    
    def tearDown(self):
        """Clean up test case."""
        print("\nCleaning up image processing test")
        if hasattr(self, 'camera'):
            self.camera.release()
    
    def test_colormap_application(self):
        """Test colormap application."""
        print("\nTesting colormap application")
        ret, frame = self.camera.read()
        self.assertTrue(ret)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Test different colormaps
        colormaps = [
            cv2.COLORMAP_HOT,    # Iron
            cv2.COLORMAP_JET,    # Rainbow
            cv2.COLORMAP_BONE    # Gray
        ]
        
        for cmap in colormaps:
            colored = cv2.applyColorMap(gray, cmap)
            self.assertEqual(colored.shape, (192, 256, 3))
            self.assertTrue(np.any(colored > 0))
        print("Colormap application test passed")
    
    def test_frame_conversion(self):
        """Test frame color space conversion."""
        print("\nTesting frame conversion")
        ret, frame = self.camera.read()
        self.assertTrue(ret)
        
        # BGR to RGB conversion
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.assertEqual(rgb.shape, frame.shape)
        self.assertFalse(np.array_equal(rgb, frame))
        
        # RGB back to BGR
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        np.testing.assert_array_equal(bgr, frame)
        print("Frame conversion test passed")

if __name__ == '__main__':
    unittest.main(verbosity=2)