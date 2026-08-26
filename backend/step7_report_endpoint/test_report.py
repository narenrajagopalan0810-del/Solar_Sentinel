"""
SonarSentinel — Step 7: Report Export Endpoint Tests
===================================================
Tests the POST /report endpoint in isolation.
"""

import io
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from step7_report_endpoint.report import router

# ---------------------------------------------------------------------------
# Minimal FastAPI app for isolated testing
# ---------------------------------------------------------------------------
app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)

# ---------------------------------------------------------------------------
# Mock Request Data
# ---------------------------------------------------------------------------
MOCK_PAYLOAD = {
    "mission_id": "MSN-TEST-123",
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
            "shadow_detected": True,
            "acoustic_score": 0.75,
            "final_score": 0.83,
            "hazard_level": "CRITICAL"
        }
    ]
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_export_report_json():
    """Verifies that the endpoint exports correct JSON formatting and headers."""
    res = client.post("/api/report?format=json", json=MOCK_PAYLOAD)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/json"
    assert "attachment; filename=SonarSentinel_Report_MSN-TEST-123.json" in res.headers["content-disposition"]
    
    data = res.json()
    assert data["mission_id"] == "MSN-TEST-123"
    assert data["mission_name"] == "MoES-Chennai-GhostNet-Audit"
    assert len(data["detections"]) == 1
    assert data["detections"][0]["detection_id"] == "DET-01"
    assert data["detections"][0]["class_name"] == "ghost_net"
    assert data["detections"][0]["bbox"]["width"] == 50.0


def test_export_report_csv():
    """Verifies that the endpoint exports correct CSV layout, headers, and rows."""
    res = client.post("/api/report?format=csv", json=MOCK_PAYLOAD)
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=SonarSentinel_Report_MSN-TEST-123.csv" in res.headers["content-disposition"]

    lines = res.text.strip().split("\r\n")
    # Verify metadata header rows
    assert lines[0] == "# SonarSentinel Mission Export Report"
    assert lines[1] == "# Mission ID,MSN-TEST-123"
    assert lines[2] == "# Mission Name,MoES-Chennai-GhostNet-Audit"
    assert lines[3] == "# Vessel Lat,13.0827"
    assert lines[4] == "# Vessel Lon,80.2707"
    
    # Find table header and rows (skipping empty lines and comments)
    table_lines = [l for l in lines if not l.startswith("#") and l != ""]
    assert len(table_lines) == 2  # 1 header + 1 data row
    
    headers = table_lines[0].split(",")
    row = table_lines[1].split(",")
    
    assert headers[0] == "Detection ID"
    assert headers[1] == "Class Name"
    assert headers[2] == "Confidence"
    assert headers[3] == "Latitude (WGS84)"
    assert headers[4] == "Longitude (WGS84)"
    assert headers[11] == "Thumbnail Crop Path"
    
    assert row[0] == "DET-01"
    assert row[1] == "ghost_net"
    assert row[2] == "0.88"
    assert row[3] == "13.082600"
    assert row[4] == "80.270800"
    assert row[11] == "uploads/crops/crop_DET-01.png"


def test_export_report_invalid_format():
    """Verifies that an unsupported format returns HTTP 422 Unprocessable Entity."""
    res = client.post("/api/report?format=pdf", json=MOCK_PAYLOAD)
    assert res.status_code == 422
