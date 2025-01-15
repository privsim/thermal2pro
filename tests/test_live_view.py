import pytest
import numpy as np
import time
from thermal2pro.ui.live_view import LiveViewHandler

@pytest.fixture
def live_view():
    return LiveViewHandler(buffer_size=5)

@pytest.fixture
def test_frame():
    return np.zeros((192, 256, 3), dtype=np.uint8)

def test_frame_processing(live_view, test_frame):
    # Process a frame and check results
    frame, metrics = live_view.process_frame(test_frame)
    assert frame is not None
    assert metrics.fps >= 0
    assert metrics.frame_time > 0
    assert metrics.dropped_frames == 0
    assert 0 <= metrics.buffer_usage <= 1

def test_buffer_management(live_view, test_frame):
    # Fill buffer
    for _ in range(10):  # More than buffer size
        live_view.process_frame(test_frame)
    
    # Check buffer size hasn't exceeded max
    assert live_view.get_metrics().buffer_usage <= 1.0
    
    # Check we can get latest frame
    latest = live_view.get_latest_frame()
    assert latest is not None
    assert latest.shape == test_frame.shape

def test_frame_skipping(live_view, test_frame):
    # Simulate slow processing
    time.sleep(0.1)  # 100ms frame time
    frame, metrics = live_view.process_frame(test_frame)
    
    # Process more frames quickly
    for _ in range(5):
        live_view.process_frame(test_frame)
    
    # Should have some dropped frames due to initial delay
    assert metrics.dropped_frames > 0

def test_metrics_calculation(live_view, test_frame):
    # Process multiple frames with known timing
    for _ in range(3):
        time.sleep(0.033)  # ~30 FPS
        live_view.process_frame(test_frame)
    
    metrics = live_view.get_metrics()
    assert 20 <= metrics.fps <= 40  # Allow some margin for system timing
    assert 0.02 <= metrics.frame_time <= 0.05

def test_buffer_clearing(live_view, test_frame):
    # Fill buffer
    for _ in range(5):
        live_view.process_frame(test_frame)
    
    # Clear buffer
    live_view.clear_buffer()
    
    # Check buffer is empty
    assert live_view.get_latest_frame() is None
    assert live_view.get_metrics().buffer_usage == 0

def test_high_fps_handling(live_view, test_frame):
    # Simulate very fast frame processing
    for _ in range(10):
        live_view.process_frame(test_frame)
    
    metrics = live_view.get_metrics()
    # Should have some dropped frames due to frame skipping at high FPS
    assert metrics.dropped_frames > 0

def test_thread_safety(live_view, test_frame):
    import threading
    import queue
    
    errors = queue.Queue()
    
    def process_frames():
        try:
            for _ in range(100):
                live_view.process_frame(test_frame)
        except Exception as e:
            errors.put(e)
    
    # Create multiple threads to process frames
    threads = [
        threading.Thread(target=process_frames)
        for _ in range(3)
    ]
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    # Check for any errors
    assert errors.empty(), f"Errors occurred: {list(errors.queue)}"

def test_performance_under_load(live_view, test_frame):
    # Process many frames quickly
    start_time = time.time()
    frames_processed = 0
    
    # Process frames for about 100ms
    while time.time() - start_time < 0.1:
        live_view.process_frame(test_frame)
        frames_processed += 1
    
    metrics = live_view.get_metrics()
    # Should maintain reasonable performance
    assert metrics.fps > 0
    assert metrics.buffer_usage <= 1.0