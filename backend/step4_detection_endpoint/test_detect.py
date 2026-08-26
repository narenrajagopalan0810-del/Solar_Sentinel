"""
SonarSentinel — Step 4: Detection Endpoint Tests
=================================================
Tests the POST /detect endpoint in complete isolation — no acoustic filter,
no geolocation. Verifies the full chain:

    upload image → preprocessing → inference → raw JSON response

Run with:
    cd backend/
    pytest step4_detection_endpoint/test_detect.py -v
"""

import io
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the Step 4 router
from step4_detection_endpoint.detect import router, _run_self_test

# ---------------------------------------------------------------------------
# Minimal FastAPI app — only the /detect route, nothing else
# This is what "test in isolation" means from the build order
# ---------------------------------------------------------------------------
app = FastAPI(title="Step4-Test")
app.include_router(router)
client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: generate a synthetic sonar PNG image as bytes
# ---------------------------------------------------------------------------
def _make_sonar_image(
    width: int = 600,
    height: int = 400,
    with_highlight: bool = True
) -> bytes:
    """
    Creates a minimal synthetic sonar image:
    - Grey seafloor background (~80 intensity)
    - One bright acoustic highlight patch (~240 intensity)
    - One dark shadow zone (~10 intensity)
    """
    img = np.zeros((height, width), dtype=np.uint8) + 80
    if with_highlight:
        img[150:200, 360:430] = 240   # highlight
        img[150:200, 430:490] = 10    # shadow
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


# ---------------------------------------------------------------------------
# Test 1 — Endpoint returns HTTP 200 and correct top-level fields
# ---------------------------------------------------------------------------
def test_detect_returns_200():
    img_bytes = _make_sonar_image()
    response = client.post(
        "/api/detect",
        files={"file": ("test_sonar.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    # Top-level keys must all be present
    assert "status"             in data
    assert "mode"               in data
    assert "image_width"        in data
    assert "image_height"       in data
    assert "total_detections"   in data
    assert "processing_time_ms" in data
    assert "navigation"         in data
    assert "detections"         in data


# ---------------------------------------------------------------------------
# Test 2 — Mode is always ONNX or DUMMY (never anything else)
# ---------------------------------------------------------------------------
def test_mode_is_valid():
    img_bytes = _make_sonar_image()
    response = client.post(
        "/api/detect",
        files={"file": ("sonar.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] in ("ONNX", "DUMMY")


# ---------------------------------------------------------------------------
# Test 3 — Image dimensions are correctly reported
# ---------------------------------------------------------------------------
def test_image_dimensions_reported():
    img_bytes = _make_sonar_image(width=600, height=400)
    response = client.post(
        "/api/detect",
        files={"file": ("sonar.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_width"]  == 600
    assert data["image_height"] == 400


# ---------------------------------------------------------------------------
# Test 4 — Each detection has the required raw fields
# ---------------------------------------------------------------------------
def test_detection_fields_present():
    img_bytes = _make_sonar_image()
    response = client.post(
        "/api/detect",
        files={"file": ("sonar.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    for det in data["detections"]:
        assert "detection_id" in det
        assert "class_name"   in det
        assert "confidence"   in det
        assert "bbox"         in det
        assert "shadow_detected" in det
        assert "acoustic_details" in det
        assert "latitude" in det
        assert "longitude" in det
        assert "geotag_details" in det

        bbox = det["bbox"]
        assert "x1"     in bbox
        assert "y1"     in bbox
        assert "x2"     in bbox
        assert "y2"     in bbox
        assert "width"  in bbox
        assert "height" in bbox


# ---------------------------------------------------------------------------
# Test 5 — Confidence scores are in valid range [0.0, 1.0]
# ---------------------------------------------------------------------------
def test_confidence_in_range():
    img_bytes = _make_sonar_image()
    response = client.post(
        "/api/detect",
        files={"file": ("sonar.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    for det in data["detections"]:
        assert 0.0 <= det["confidence"] <= 1.0, (
            f"Confidence {det['confidence']} out of [0.0, 1.0]"
        )


# ---------------------------------------------------------------------------
# Test 6 — Bounding box coordinates are within image bounds
# ---------------------------------------------------------------------------
def test_bbox_within_image_bounds():
    w, h = 600, 400
    img_bytes = _make_sonar_image(width=w, height=h)
    response = client.post(
        "/api/detect",
        files={"file": ("sonar.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    for det in data["detections"]:
        bbox = det["bbox"]
        assert bbox["x1"] >= 0,       f"x1={bbox['x1']} < 0"
        assert bbox["y1"] >= 0,       f"y1={bbox['y1']} < 0"
        assert bbox["x2"] <= w,       f"x2={bbox['x2']} > image width {w}"
        assert bbox["y2"] <= h,       f"y2={bbox['y2']} > image height {h}"
        assert bbox["x2"] > bbox["x1"], "x2 must be > x1"
        assert bbox["y2"] > bbox["y1"], "y2 must be > y1"


# ---------------------------------------------------------------------------
# Test 7 — Class names are from the known target class set
# ---------------------------------------------------------------------------
VALID_CLASSES = {"ghost_net", "cylinder", "pipe", "wreckage", "unknown_anomaly"}

def test_class_names_are_valid():
    img_bytes = _make_sonar_image()
    response = client.post(
        "/api/detect",
        files={"file": ("sonar.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    for det in data["detections"]:
        assert det["class_name"] in VALID_CLASSES, (
            f"Unknown class '{det['class_name']}'"
        )


# ---------------------------------------------------------------------------
# Test 8 — Empty / corrupt file returns 400
# ---------------------------------------------------------------------------
def test_empty_file_returns_400():
    response = client.post(
        "/api/detect",
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Test 9 — Unsupported file type returns 415
# ---------------------------------------------------------------------------
def test_unsupported_type_returns_415():
    response = client.post(
        "/api/detect",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert response.status_code == 415


# ---------------------------------------------------------------------------
# Test 10 — Self-test helper runs without exception
# ---------------------------------------------------------------------------
def test_self_test_helper():
    result = _run_self_test()
    assert "mode"       in result
    assert "detections" in result
    assert result["mode"] in ("ONNX", "DUMMY")
