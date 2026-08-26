"""
SonarSentinel — Step 5: Acoustic Noise Filter Tests
===================================================
Tests the physics-informed highlight-to-shadow check in noise_filter.py.
Verifies that:
  - Bounding boxes on starboard side scan to the right (+X).
  - Bounding boxes on port side scan to the left (-X).
  - Detections with a valid shadow keep their raw confidence.
  - Detections with no shadow (or weak shadow) are penalized sharply.
"""

import pytest
import numpy as np
from step5_acoustic_filter.noise_filter import (
    inspect_shadow_presence,
    apply_acoustic_filter,
    CONFIDENCE_PENALTY_FACTOR
)


@pytest.fixture
def base_seafloor():
    """Generates a synthetic 400x800 seafloor image with flat background (intensity 100)."""
    return np.ones((400, 800), dtype=np.uint8) * 100


def test_starboard_valid_shadow(base_seafloor):
    """
    If a target is placed on the starboard side (x > 400),
    the shadow region lies to its right (+X).
    A dark region in the shadow zone should trigger positive shadow detection.
    """
    img = base_seafloor.copy()
    
    # 1. Starboard bbox (highlight)
    # x1=500, x2=550. Center = 525 (starboard)
    y1, y2 = 150, 200
    x1, x2 = 500, 550
    img[y1:y2, x1:x2] = 230  # High intensity reflection
    
    # 2. Add trailing dark shadow (to the right, +X direction)
    img[y1:y2, x2:x2 + 80] = 15  # Very dark shadow
    
    shadow_detected, shadow_mean, bg_mean, contrast, details = inspect_shadow_presence(
        img, x1, y1, x2, y2, sonar_type="sidescan"
    )
    
    assert shadow_detected is True
    assert details["look_direction"] == "starboard"
    assert shadow_mean < bg_mean * 0.85
    assert contrast > 2.0


def test_port_valid_shadow(base_seafloor):
    """
    If a target is placed on the port side (x < 400),
    the shadow region lies to its left (-X).
    """
    img = base_seafloor.copy()
    
    # 1. Port bbox (highlight)
    # x1=200, x2=250. Center = 225 (port)
    y1, y2 = 100, 150
    x1, x2 = 200, 250
    img[y1:y2, x1:x2] = 240
    
    # 2. Add trailing dark shadow (to the left, -X direction)
    img[y1:y2, x1 - 80:x1] = 10
    
    shadow_detected, _, _, _, details = inspect_shadow_presence(
        img, x1, y1, x2, y2, sonar_type="sidescan"
    )
    
    assert shadow_detected is True
    assert details["look_direction"] == "port"


def test_no_shadow_downgrade(base_seafloor):
    """
    If there is no shadow trailing the highlight,
    the confidence score should be penalized sharply by the filter.
    """
    img = base_seafloor.copy()
    
    # Starboard highlight, but no shadow (trailing region is normal seafloor, intensity 100)
    y1, y2 = 150, 200
    x1, x2 = 500, 550
    img[y1:y2, x1:x2] = 220
    
    detections = [{
        "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "width": x2-x1, "height": y2-y1},
        "confidence": 0.90,
        "class_name": "ghost_net"
    }]
    
    filtered = apply_acoustic_filter(img, detections, sonar_type="sidescan")
    
    assert len(filtered) == 1
    assert filtered[0]["shadow_detected"] is False
    # Raw confidence 0.90 should be multiplied by the penalty factor (e.g. 0.3)
    assert filtered[0]["confidence"] == pytest.approx(0.90 * CONFIDENCE_PENALTY_FACTOR)


def test_with_shadow_retains_confidence(base_seafloor):
    """
    If a valid shadow is present, the confidence score must not change.
    """
    img = base_seafloor.copy()
    
    y1, y2 = 150, 200
    x1, x2 = 500, 550
    img[y1:y2, x1:x2] = 240
    img[y1:y2, x2:x2 + 80] = 12  # shadow
    
    detections = [{
        "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "width": x2-x1, "height": y2-y1},
        "confidence": 0.85,
        "class_name": "wreckage"
    }]
    
    filtered = apply_acoustic_filter(img, detections, sonar_type="sidescan")
    
    assert len(filtered) == 1
    assert filtered[0]["shadow_detected"] is True
    assert filtered[0]["confidence"] == 0.85
