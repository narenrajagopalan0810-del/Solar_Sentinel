"""
SonarSentinel — Step 5: Acoustic Noise Filter (noise_filter.py)
==============================================================
Build Order Reference : SonarSentinel_Backend_Build_Order.txt  →  Step 5
Depends on           : Step 4 (POST /detect endpoint)

WHAT THIS FILE DOES
-------------------
Implements a physics-based highlight-to-shadow verification step:
  1. For each detection, it identifies the sonar's look direction
     (port vs. starboard) based on nadir division (image width / 2).
  2. Extracts the region trailing the bounding box along the acoustic
     propagation path.
  3. Measures the average intensity of the trailing region (shadow candidate)
     against the local seafloor background.
  4. If no shadow is detected (high reflectivity or similar brightness to
     background), it downgrades the detection confidence sharply.
"""

import logging
from typing import Dict, Any, List, Tuple
import numpy as np

logger = logging.getLogger("sonarsentinel.step5.noise_filter")

# Heuristic parameters (tuned for typical 8-bit side-scan sonar image returns)
DEFAULT_SHADOW_LENGTH_PX = 80
DEFAULT_BG_PAD_PX = 30
CONTRAST_RATIO_THRESHOLD = 1.25  # Highlight mean / Shadow mean
SHADOW_REF_RATIO = 0.85          # Shadow mean / Background mean (must be less than this to count as shadow)
CONFIDENCE_PENALTY_FACTOR = 0.3  # Multiply confidence by this if no shadow is found


def inspect_shadow_presence(
    image_gray: np.ndarray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    sonar_type: str = "sidescan"
) -> Tuple[bool, float, float, float, Dict[str, Any]]:
    """
    Analyzes the trailing region of a bounding box for an acoustic shadow.

    Acoustic Ray Tracing Principle:
    A real 3D object rising above the seafloor intercepts the acoustic beam.
    This creates:
      - A bright return (highlight) on the side facing the transducer.
      - A dark region (occlusion/shadow) behind the object, in the direction
        of acoustic wave propagation.
    A false positive (surface noise, seabed speckle) will not cast a shadow.

    Returns:
        shadow_detected (bool): True if a valid acoustic shadow exists trailing the box.
        shadow_mean (float): Average gray level of the shadow search zone [0-255].
        bg_mean (float): Average gray level of the local seafloor background [0-255].
        contrast_ratio (float): Ratio of highlight intensity to shadow intensity.
        details (dict): Comprehensive dictionary of computed metrics for reporting.
    """
    h, w = image_gray.shape

    # Clamp bbox coordinates to image dimensions
    x1_cl = max(0, min(int(x1), w - 1))
    y1_cl = max(0, min(int(y1), h - 1))
    x2_cl = max(x1_cl + 1, min(int(x2), w))
    y2_cl = max(y1_cl + 1, min(int(y2), h))

    box_w = x2_cl - x1_cl
    box_h = y2_cl - y1_cl

    # 1. Compute highlight stats (inside bounding box)
    highlight_roi = image_gray[y1_cl:y2_cl, x1_cl:x2_cl]
    highlight_mean = float(np.mean(highlight_roi)) if highlight_roi.size > 0 else 128.0

    # 2. Determine acoustic look direction & shadow search coordinates
    # For side-scan, nadir is at w // 2. Starboard casts right (+X), Port casts left (-X).
    center_x = (x1_cl + x2_cl) / 2.0
    shadow_length = min(DEFAULT_SHADOW_LENGTH_PX, max(int(box_w * 2.0), 30))

    if sonar_type == "sidescan":
        look_direction = "starboard" if center_x >= (w / 2.0) else "port"
        if look_direction == "starboard":
            sx1 = x2_cl
            sx2 = min(w, x2_cl + shadow_length)
            sy1 = max(0, y1_cl - 2)
            sy2 = min(h, y2_cl + 2)
        else:  # port
            sx1 = max(0, x1_cl - shadow_length)
            sx2 = x1_cl
            sy1 = max(0, y1_cl - 2)
            sy2 = min(h, y2_cl + 2)
    else:
        # FLS: looks from top to bottom (+Y)
        look_direction = "forward"
        sx1 = max(0, x1_cl - 2)
        sx2 = min(w, x2_cl + 2)
        sy1 = y2_cl
        sy2 = min(h, y2_cl + shadow_length)

    # 3. Extract shadow region
    if sx2 > sx1 and sy2 > sy1:
        shadow_roi = image_gray[sy1:sy2, sx1:sx2]
        shadow_mean = float(np.mean(shadow_roi)) if shadow_roi.size > 0 else highlight_mean
    else:
        shadow_mean = highlight_mean

    # 4. Extract local background reference (annular margin around the highlight + shadow)
    bg_pad = DEFAULT_BG_PAD_PX
    bx1 = max(0, min(x1_cl, sx1) - bg_pad)
    by1 = max(0, min(y1_cl, sy1) - bg_pad)
    bx2 = min(w, max(x2_cl, sx2) + bg_pad)
    by2 = min(h, max(y2_cl, sy2) + bg_pad)

    # We mask out the target and the shadow to get clean seafloor background
    bg_roi = image_gray[by1:by2, bx1:bx2].copy()
    
    # Calculate mask in local coordinates
    local_x1 = x1_cl - bx1
    local_y1 = y1_cl - by1
    local_x2 = x2_cl - bx1
    local_y2 = y2_cl - by1

    local_sx1 = sx1 - bx1
    local_sy1 = sy1 - by1
    local_sx2 = sx2 - bx1
    local_sy2 = sy2 - by1

    mask = np.ones_like(bg_roi, dtype=bool)
    mask[local_y1:local_y2, local_x1:local_x2] = False
    if local_sx2 > local_sx1 and local_sy2 > local_sy1:
        mask[local_sy1:local_sy2, local_sx1:local_sx2] = False

    bg_pixels = bg_roi[mask]
    bg_mean = float(np.mean(bg_pixels)) if bg_pixels.size > 0 else 100.0

    # 5. Physics check
    contrast_ratio = highlight_mean / max(shadow_mean, 1.0)
    
    # Condition A: Shadow region is significantly darker than surrounding seafloor
    is_darker_than_bg = (shadow_mean < bg_mean * SHADOW_REF_RATIO)
    # Condition B: High contrast ratio between reflection highlight and occlusion zone,
    # but the shadow region itself must still be at least slightly darker than the background seafloor
    is_high_contrast = (contrast_ratio >= CONTRAST_RATIO_THRESHOLD) and (shadow_mean < bg_mean * 0.95)

    shadow_detected = is_darker_than_bg or is_high_contrast

    details = {
        "look_direction": look_direction,
        "highlight_mean": round(highlight_mean, 2),
        "shadow_mean": round(shadow_mean, 2),
        "bg_mean": round(bg_mean, 2),
        "contrast_ratio": round(contrast_ratio, 2),
        "is_darker_than_bg": bool(is_darker_than_bg),
        "is_high_contrast": bool(is_high_contrast),
        "shadow_length_px": shadow_length
    }

    return shadow_detected, shadow_mean, bg_mean, contrast_ratio, details


def apply_acoustic_filter(
    image_gray: np.ndarray,
    detections: List[Dict[str, Any]],
    sonar_type: str = "sidescan",
    penalty_factor: float = CONFIDENCE_PENALTY_FACTOR
) -> List[Dict[str, Any]]:
    """
    Processes a list of raw detections:
      1. Inspects the trailing shadow region for each bounding box.
      2. If no shadow is detected, downgrades raw confidence sharply.
      3. Updates detection dictionaries in place.

    Expected format per detection:
      {
         "bbox": {"x1": float, "y1": float, "x2": float, "y2": float, ...},
         "confidence": float,
         "class_name": str,
         ...
      }
    """
    filtered_detections = []
    
    for det in detections:
        # Clone to avoid mutating original dictionary if shared
        d = dict(det)
        bbox = d["bbox"]
        
        # Unpack box coordinates
        x1, y1 = bbox["x1"], bbox["y1"]
        x2, y2 = bbox["x2"], bbox["y2"]
        
        # Run physical shadow inspection
        shadow_detected, shadow_mean, bg_mean, contrast_ratio, details = inspect_shadow_presence(
            image_gray=image_gray,
            x1=x1, y1=y1, x2=x2, y2=y2,
            sonar_type=sonar_type
        )
        
        raw_conf = d["confidence"]
        
        # Apply penalty if no shadow is found
        if not shadow_detected:
            new_conf = round(raw_conf * penalty_factor, 3)
            logger.info(
                f"[Acoustic Filter] No shadow found for {d['class_name']} "
                f"at ({x1},{y1}). Downgrading confidence {raw_conf} -> {new_conf}"
            )
        else:
            new_conf = raw_conf
            logger.debug(
                f"[Acoustic Filter] Shadow confirmed for {d['class_name']} "
                f"at ({x1},{y1}). Keeping confidence {raw_conf}"
            )
            
        d["confidence"] = new_conf
        d["shadow_detected"] = shadow_detected
        d["acoustic_details"] = details
        
        filtered_detections.append(d)
        
    return filtered_detections
