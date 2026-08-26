"""
SonarSentinel — Step 4: Detection Endpoint (detect.py)
=======================================================
Build Order Reference : SonarSentinel_Backend_Build_Order.txt  →  Step 4
Depends on           : Step 2 (inference.py)  +  Step 3 (preprocessing)

WHAT THIS FILE DOES
-------------------
Adds a POST /detect endpoint that:
  1. Accepts an uploaded sonar image (PNG / JPG / TIFF)
  2. Runs it through the preprocessing pipeline (Bilateral + CLAHE)
  3. Passes the preprocessed frame to the ONNX inference session
  4. Returns RAW detections as clean JSON — no acoustic filter, no
     geolocation (those come in Steps 5 and 6)

RAW response shape
------------------
{
  "status":           "ok",
  "mode":             "ONNX" | "DUMMY",
  "image_width":      int,
  "image_height":     int,
  "total_detections": int,
  "processing_time_ms": float,
  "detections": [
    {
      "detection_id": "DET-01",
      "class_name":   "ghost_net",
      "confidence":   0.87,
      "bbox": {
        "x1": 120.5, "y1": 80.3,
        "x2": 200.1, "y2": 140.6,
        "width": 79.6, "height": 60.3
      }
    }
  ]
}

INTEGRATION INTO main.py
-------------------------
  from step4_detection_endpoint.detect import router as detect_router
  app.include_router(detect_router)
"""

import time
import logging
from typing import List, Dict, Any, Optional

import cv2
import numpy as np

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Step 2 — ONNX inference session singleton
# ---------------------------------------------------------------------------
import sys
from pathlib import Path
# Make sure parent packages are importable when running from any cwd
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from step2_model_loading.inference import onnx_session

# ---------------------------------------------------------------------------
# Step 3 — Preprocessing pipeline (already in repo at app/services/preprocessing.py)
# We import directly from the existing service so there is no code duplication.
# ---------------------------------------------------------------------------
from app.services.preprocessing import load_image_from_bytes, preprocess_sonar_image

# ---------------------------------------------------------------------------
# Step 5 — Acoustic Noise Filter
# ---------------------------------------------------------------------------
from step5_acoustic_filter.noise_filter import apply_acoustic_filter

# ---------------------------------------------------------------------------
# Step 6 — Geotagging Engine
# ---------------------------------------------------------------------------
from step6_geotagging.geotag import generate_simulated_navigation_sidecar, georeference_detections

logger = logging.getLogger("sonarsentinel.step4.detect")

# ---------------------------------------------------------------------------
# Pydantic response schemas — raw, minimal, exactly what Step 4 needs
# ---------------------------------------------------------------------------

class RawBoundingBox(BaseModel):
    """Pixel-space bounding box in the original (un-resized) image."""
    x1: float = Field(..., description="Top-left X pixel coordinate")
    y1: float = Field(..., description="Top-left Y pixel coordinate")
    x2: float = Field(..., description="Bottom-right X pixel coordinate")
    y2: float = Field(..., description="Bottom-right Y pixel coordinate")
    width:  float = Field(..., description="Box width in pixels")
    height: float = Field(..., description="Box height in pixels")


class RawDetection(BaseModel):
    """Single raw detection — with acoustic shadow filter (Step 5) and georeferencing (Step 6)."""
    detection_id: str  = Field(..., description="Sequential ID e.g. DET-01")
    class_name:   str  = Field(..., description="Predicted target class")
    confidence:   float = Field(..., description="ONNX confidence score (potentially downgraded by acoustic filter)")
    bbox: RawBoundingBox
    shadow_detected: bool = Field(..., description="True if acoustic shadow signature was identified trailing the target")
    acoustic_details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed physical metrics computed by the acoustic filter")
    latitude: float = Field(..., description="Estimated WGS84 latitude")
    longitude: float = Field(..., description="Estimated WGS84 longitude")
    geotag_details: Optional[Dict[str, Any]] = Field(default=None, description="Calculated slant-to-ground swath projection parameters")


class DetectResponse(BaseModel):
    """Full /detect response — raw pipeline output only."""
    status:             str   = Field(default="ok")
    mode:               str   = Field(..., description="'ONNX' when model is loaded, 'DUMMY' otherwise")
    image_width:        int
    image_height:       int
    total_detections:   int
    processing_time_ms: float = Field(..., description="End-to-end latency in milliseconds")
    navigation:         Optional[Dict[str, Any]] = Field(default=None, description="Ingested/simulated telemetry sidecar parameters")
    detections:         List[RawDetection]


# ---------------------------------------------------------------------------
# Allowed image MIME types
# ---------------------------------------------------------------------------
ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/x-tiff",
    "application/octet-stream",  # some multipart senders omit proper MIME
}

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api", tags=["Step 4 — Detection"])


@router.post(
    "/detect",
    response_model=DetectResponse,
    summary="Raw Sonar Detection — Step 4",
    description=(
        "Upload a sonar image (PNG/JPG/TIFF). "
        "The image is preprocessed (Bilateral despeckling + CLAHE) then "
        "passed to the ONNX inference session. "
        "Returns raw bounding boxes, class labels, and confidence scores. "
        "No acoustic filter or geotagging is applied at this stage."
    ),
)
async def detect(
    file: UploadFile = File(
        ...,
        description="Sonar image file — PNG, JPG, or TIFF (8-bit or 16-bit grayscale/RGB)"
    ),
    conf_threshold: float = Query(
        default=0.25,
        ge=0.01,
        le=0.99,
        description="Minimum confidence threshold for detections (default 0.25)"
    ),
):
    """
    POST /api/detect

    Pipeline executed per request:
      1. Validate file type and read bytes
      2. Decode bytes → OpenCV numpy array
      3. Bilateral despeckling + CLAHE contrast enhancement
      4. ONNX / Dummy inference  → raw boxes, labels, scores
      5. Package into DetectResponse JSON

    Steps 5-8 (acoustic filter, geolocation, report, CORS) are NOT
    applied here — this endpoint is intentionally minimal so it can be
    tested in complete isolation.
    """
    t_start = time.perf_counter()

    # ── 1. File validation ────────────────────────────────────────────────
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                "Please upload a PNG, JPG, or TIFF sonar image."
            ),
        )

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(image_bytes) > 50 * 1024 * 1024:  # 50 MB hard limit
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum allowed size is 50 MB."
        )

    # ── 2. Decode bytes → numpy ───────────────────────────────────────────
    try:
        raw_image = load_image_from_bytes(image_bytes)
    except Exception as exc:
        logger.warning(f"[Step 4] Image decode failed: {exc}")
        raise HTTPException(
            status_code=400,
            detail=f"Could not decode image: {exc}. "
                   "Ensure the file is a valid PNG/JPG/TIFF sonar image."
        )

    # ── 3. Preprocessing — Bilateral despeckling + CLAHE ─────────────────
    try:
        preproc = preprocess_sonar_image(raw_image)
        proc_bgr = preproc["processed_bgr"]   # 3-channel uint8, YOLO-ready
        img_h    = preproc["height"]
        img_w    = preproc["width"]
    except Exception as exc:
        logger.error(f"[Step 4] Preprocessing failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Preprocessing pipeline error: {exc}"
        )

    # ── 4. ONNX / Dummy Inference ─────────────────────────────────────────
    try:
        boxes, labels, scores = onnx_session.run(proc_bgr, conf_threshold=conf_threshold)
    except RuntimeError as exc:
        # OnnxInferenceSession raises RuntimeError only if _loaded=True but
        # session is somehow None — should never happen in normal operation.
        logger.error(f"[Step 4] Inference session error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Inference error: {exc}")
    except Exception as exc:
        logger.error(f"[Step 4] Unexpected inference error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Inference error: {exc}")

    # ── 5. Build raw detection list as dicts ──────────────────────────────
    raw_list = []
    for idx, (box, label, score) in enumerate(zip(boxes, labels, scores)):
        raw_list.append({
            "detection_id": f"DET-{idx + 1:02d}",
            "class_name": label,
            "confidence": score,
            "bbox": {
                "x1": box["x1"],
                "y1": box["y1"],
                "x2": box["x2"],
                "y2": box["y2"],
                "width": box["width"],
                "height": box["height"]
            }
        })

    # ── 6. Apply Step 5 Acoustic Shadow Noise Filter ────────────────────────
    try:
        filtered_list = apply_acoustic_filter(
            image_gray=preproc["processed"],
            detections=raw_list,
            sonar_type="sidescan"
        )
    except Exception as exc:
        logger.error(f"[Step 5] Acoustic filter failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Acoustic shadow verification failed: {exc}")

    # ── 7. Generate Step 6 Navigation Sidecar Telemetry ─────────────────────
    nav_sidecar = generate_simulated_navigation_sidecar(file.filename)

    # ── 8. Apply Step 6 Geotagging Engine ───────────────────────────────────
    try:
        geotagged_list = georeference_detections(
            detections=filtered_list,
            image_width=img_w,
            image_height=img_h,
            nav=nav_sidecar
        )
    except Exception as exc:
        logger.error(f"[Step 6] Geotagging failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Georeferencing projection failed: {exc}")

    # ── 9. Map to Pydantic Response Schema ──────────────────────────────────
    detections: List[RawDetection] = []
    for d in geotagged_list:
        detections.append(
            RawDetection(
                detection_id=d["detection_id"],
                class_name=d["class_name"],
                confidence=d["confidence"],
                bbox=RawBoundingBox(**d["bbox"]),
                shadow_detected=d["shadow_detected"],
                acoustic_details=d["acoustic_details"],
                latitude=d["latitude"],
                longitude=d["longitude"],
                geotag_details=d["geotag_details"]
            )
        )

    elapsed_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    logger.info(
        f"[Step 4] /detect complete — mode={onnx_session.mode} "
        f"detections={len(detections)} time={elapsed_ms}ms"
    )

    return DetectResponse(
        mode=onnx_session.mode,
        image_width=img_w,
        image_height=img_h,
        total_detections=len(detections),
        processing_time_ms=elapsed_ms,
        navigation=nav_sidecar.model_dump(),
        detections=detections,
    )


# ---------------------------------------------------------------------------
# Quick self-test helper (not a route — import and call in pytest or manually)
# ---------------------------------------------------------------------------
def _run_self_test() -> dict:
    """
    Generates a synthetic sonar image and calls the pipeline directly
    (without HTTP) to verify the full Step 4 chain works end-to-end.

    Usage:
        python -c "from step4_detection_endpoint.detect import _run_self_test; _run_self_test()"
    """
    import io

    # Build a minimal 400×600 synthetic sonar image with one bright highlight
    img = np.zeros((400, 600), dtype=np.uint8) + 80    # grey seafloor
    img[150:200, 360:430] = 240                         # acoustic highlight
    img[150:200, 430:490] = 10                          # acoustic shadow

    _, buf = cv2.imencode(".png", img)
    raw_bytes = buf.tobytes()

    # Replicate the pipeline exactly as the endpoint does
    raw_image = load_image_from_bytes(raw_bytes)
    preproc   = preprocess_sonar_image(raw_image)
    boxes, labels, scores = onnx_session.run(
        preproc["processed_bgr"], conf_threshold=0.25
    )

    result = {
        "mode":       onnx_session.mode,
        "detections": len(boxes),
        "labels":     labels,
        "scores":     scores,
        "boxes":      boxes,
    }
    print(f"[Step 4 Self-Test] {result}")
    return result


if __name__ == "__main__":
    _run_self_test()
