import pytest
import numpy as np
import cv2
from thermal2pro.camera.processing import ThermalProcessor

@pytest.fixture
def thermal_processor():
    return ThermalProcessor()

@pytest.fixture
def sample_frame():
    # Create a gradient frame for testing color mapping
    frame = np.zeros((192, 256), dtype=np.uint8)
    for i in range(256):
        frame[:, i] = i
    return frame

def test_color_palette_switching(thermal_processor, sample_frame):
    # Test iron palette
    iron = thermal_processor.apply_palette(sample_frame, 'iron')
    assert iron.shape == (192, 256, 3)
    assert np.any(iron[:, -1] != iron[:, 0])  # Colors should change across gradient
    
    # Test rainbow palette
    rainbow = thermal_processor.apply_palette(sample_frame, 'rainbow')
    assert rainbow.shape == (192, 256, 3)
    assert not np.array_equal(rainbow, iron)  # Should be different from iron
    
    # Test grayscale
    gray = thermal_processor.apply_palette(sample_frame, 'gray')
    assert gray.shape == (192, 256, 3)
    assert len(np.unique(gray[:, 0])) == 1  # Each column should be same color

def test_frame_scaling(thermal_processor, sample_frame):
    # Test upscaling
    scaled_up = thermal_processor.scale_frame(sample_frame, 512, 384)
    assert scaled_up.shape == (384, 512)
    
    # Test downscaling
    scaled_down = thermal_processor.scale_frame(sample_frame, 128, 96)
    assert scaled_down.shape == (96, 128)
    
    # Test aspect ratio preservation
    scaled_ratio = thermal_processor.scale_frame(sample_frame, 512, 512)
    assert scaled_ratio.shape[1] / scaled_ratio.shape[0] == 256 / 192

def test_temperature_range_mapping(thermal_processor, sample_frame):
    # Test temperature range mapping
    min_temp, max_temp = 20.0, 40.0  # Celsius
    temp_mapped = thermal_processor.map_temperature_range(sample_frame, min_temp, max_temp)
    
    # Check that 0 maps to min_temp and 255 maps to max_temp
    assert np.isclose(thermal_processor.raw_to_temperature(0, min_temp, max_temp), min_temp)
    assert np.isclose(thermal_processor.raw_to_temperature(255, min_temp, max_temp), max_temp)

def test_frame_preprocessing(thermal_processor, sample_frame):
    # Test noise reduction
    denoised = thermal_processor.preprocess_frame(sample_frame)
    assert denoised.shape == sample_frame.shape
    assert denoised.dtype == sample_frame.dtype
    
    # Test that noise reduction smooths the image
    assert np.mean(np.abs(np.diff(denoised))) < np.mean(np.abs(np.diff(sample_frame)))

def test_invalid_palette_handling(thermal_processor, sample_frame):
    with pytest.raises(ValueError):
        thermal_processor.apply_palette(sample_frame, 'invalid_palette')

def test_invalid_frame_handling(thermal_processor):
    with pytest.raises(ValueError):
        thermal_processor.preprocess_frame(None)
    
    with pytest.raises(ValueError):
        thermal_processor.preprocess_frame(np.zeros((10, 10, 3)))  # Wrong shape
