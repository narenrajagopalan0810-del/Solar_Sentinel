import numpy as np
import pytest
from preprocess import preprocess_image

def test_output_shape_grayscale():
    fake_gray = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
    result = preprocess_image(fake_gray)
    assert result.shape == (480, 640, 3)
    assert result.dtype == np.uint8

def test_output_shape_bgr():
    fake_bgr = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = preprocess_image(fake_bgr)
    assert result.shape == (480, 640, 3)
    assert result.dtype == np.uint8

def test_output_shape_rgba():
    fake_rgba = np.random.randint(0, 255, (480, 640, 4), dtype=np.uint8)
    result = preprocess_image(fake_rgba)
    assert result.shape == (480, 640, 3)
    assert result.dtype == np.uint8

def test_inference_runs():
    from inference import run
    fake_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    detections = run(fake_image)
    assert isinstance(detections, list)
    assert len(detections) > 0
    assert "class" in detections[0]
    assert "confidence" in detections[0]
    assert "bbox" in detections[0]
