# Step 4 — Detection Endpoint

> **Build Order:** `SonarSentinel_Backend_Build_Order.txt` → Step 4  
> **Depends on:** Step 2 (`step2_model_loading/inference.py`) + Step 3 (preprocessing in `app/services/preprocessing.py`)

---

## What this step delivers

> *"Add a POST /detect endpoint that accepts an uploaded sonar image, runs it  
> through preprocessing then inference, and returns raw detections as JSON  
> (box coordinates, class, raw confidence). Test this in isolation with a  
> sample image before adding any filtering on top."*

---

## Files in this folder

| File | Purpose |
|---|---|
| `detect.py` | FastAPI router with `POST /api/detect` endpoint + Pydantic schemas |
| `test_detect.py` | 10 isolation tests — no HTTP server needed |
| `README.md` | This file |

---

## How to integrate into main.py

```python
from step4_detection_endpoint.detect import router as detect_router
app.include_router(detect_router)
```

---

## Endpoint

### `POST /api/detect`

| Field | Value |
|---|---|
| Method | `POST` |
| Content-Type | `multipart/form-data` |
| Body param | `file` — sonar image (PNG / JPG / TIFF) |
| Query param | `conf_threshold` — float 0.01–0.99 (default `0.25`) |

### Response JSON

```json
{
  "status": "ok",
  "mode": "ONNX",
  "image_width": 600,
  "image_height": 400,
  "total_detections": 2,
  "processing_time_ms": 38.5,
  "detections": [
    {
      "detection_id": "DET-01",
      "class_name": "ghost_net",
      "confidence": 0.873,
      "bbox": {
        "x1": 120.5,
        "y1": 80.3,
        "x2": 200.1,
        "y2": 140.6,
        "width": 79.6,
        "height": 60.3
      }
    }
  ]
}
```

> ⚠️ **No acoustic filter, no geotagging** — this is intentional. Steps 5 and 6 add those on top.

---

## How to test with curl

```powershell
# From backend/ with the server running
curl -X POST http://localhost:8000/api/detect `
  -F "file=@path/to/sonar_image.png" `
  -F "conf_threshold=0.25"
```

---

## How to run unit tests

```powershell
# From backend/ folder with venv active
pytest step4_detection_endpoint/test_detect.py -v
```

Expected output:
```
PASSED test_detect_returns_200
PASSED test_mode_is_valid
PASSED test_image_dimensions_reported
PASSED test_detection_fields_present
PASSED test_confidence_in_range
PASSED test_bbox_within_image_bounds
PASSED test_class_names_are_valid
PASSED test_empty_file_returns_400
PASSED test_unsupported_type_returns_415
PASSED test_self_test_helper
```

---

## Pipeline executed per request

```
Upload (multipart/form-data)
        ↓
File validation (type, size, not empty)
        ↓
Decode bytes → OpenCV numpy array
        ↓
Bilateral Despeckling + CLAHE  [Step 3 — preprocessing.py]
        ↓
ONNX Inference / DummySession  [Step 2 — inference.py]
        ↓
Raw DetectResponse JSON
        ↓
Step 5 (acoustic filter) plugs in HERE ↑ after inference
```

---

## Error responses

| Code | Cause |
|---|---|
| `400` | Empty file or corrupt / undecodable image |
| `413` | File > 50 MB |
| `415` | Unsupported MIME type (not PNG/JPG/TIFF) |
| `500` | Preprocessing or inference internal error |
