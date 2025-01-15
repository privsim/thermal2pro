import numpy as np
import cv2

class ThermalProcessor:
    PALETTE_MAP = {
        'iron': cv2.COLORMAP_HOT,
        'rainbow': cv2.COLORMAP_JET,
        'gray': cv2.COLORMAP_BONE
    }
    
    def apply_palette(self, frame, palette_name):
        """Apply color palette to grayscale frame."""
        if palette_name not in self.PALETTE_MAP:
            raise ValueError(f"Invalid palette: {palette_name}. Must be one of {list(self.PALETTE_MAP.keys())}")
        
        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError("Invalid frame")
            
        colored = cv2.applyColorMap(frame, self.PALETTE_MAP[palette_name])
        return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    
    def scale_frame(self, frame, target_width, target_height):
        """Scale frame while preserving aspect ratio."""
        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError("Invalid frame")
            
        src_aspect = frame.shape[1] / frame.shape[0]
        target_aspect = target_width / target_height
        
        if src_aspect > target_aspect:
            # Width limited
            new_width = target_width
            new_height = int(target_width / src_aspect)
        else:
            # Height limited
            new_height = target_height
            new_width = int(target_height * src_aspect)
            
        return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    
    def map_temperature_range(self, frame, min_temp, max_temp):
        """Map raw values to temperature range."""
        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError("Invalid frame")
            
        # Linear mapping from raw values to temperature
        temp_frame = self.raw_to_temperature(frame, min_temp, max_temp)
        # Normalize back to 0-255 for display
        normalized = ((temp_frame - min_temp) * 255 / (max_temp - min_temp)).astype(np.uint8)
        return normalized
    
    def raw_to_temperature(self, raw_value, min_temp, max_temp):
        """Convert raw sensor value to temperature."""
        return min_temp + (raw_value / 255.0) * (max_temp - min_temp)
    
    def preprocess_frame(self, frame):
        """Apply preprocessing to raw frame."""
        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError("Invalid frame")
            
        if len(frame.shape) != 2:
            raise ValueError("Frame must be grayscale (single channel)")
            
        # Apply bilateral filter for noise reduction while preserving edges
        denoised = cv2.bilateralFilter(frame, 5, 75, 75)
        return denoised
