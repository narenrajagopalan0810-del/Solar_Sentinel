# Step 7 — Report Export Endpoint

> **Build Order:** `SonarSentinel_Backend_Build_Order.txt` → Step 7  
> **Depends on:** Step 6 (Geotagging Engine)

---

## What this step delivers

Exposes a standalone, dedicated API endpoint that takes the final geotagged and physics-filtered list of sonar detections, along with vessel telemetry, and serializes it into:
- **JSON Report** (formatted data structures)
- **CSV Report** (tabulated spreadsheet containing bounding boxes, severity classification, coordinates, and crop paths)

This endpoint is used by the UI's **Download Report** functionality.

---

## Files in this folder

| File | Purpose |
|---|---|
| `report.py` | Defines the request body structures (`ReportRequest`), serialization helper logic, and the `POST /api/report` endpoint. |
| `test_report.py` | Contains unit tests verifying the formatting rules for JSON and CSV file outputs. |
| `README.md` | This file |

---

## API Request Specifications

### `POST /api/report?format=json` or `POST /api/report?format=csv`

#### JSON Body Payload (`ReportRequest`)
```json
{
  "mission_id": "MSN-A83FD91B",
  "mission_name": "MoES-Chennai-GhostNet-Audit",
  "vessel_lat": 13.0827,
  "vessel_lon": 80.2707,
  "heading": 85.0,
  "altitude": 18.0,
  "swath_width_m": 100.0,
  "detections": [
    {
      "detection_id": "DET-01",
      "class_name": "ghost_net",
      "confidence": 0.88,
      "bbox": {
        "x1": 100.0,
        "y1": 150.0,
        "x2": 150.0,
        "y2": 180.0,
        "width": 50.0,
        "height": 30.0
      },
      "latitude": 13.0826,
      "longitude": 80.2708,
      "crop_image_url": "uploads/crops/crop_DET-01.png",
      "shadow_detected": true,
      "acoustic_score": 0.75,
      "final_score": 0.83,
      "hazard_level": "CRITICAL"
    }
  ]
}
```

---

## How to run unit tests

From the `backend/` directory with the virtual environment active:
```powershell
pytest step7_report_endpoint/test_report.py -v
```
