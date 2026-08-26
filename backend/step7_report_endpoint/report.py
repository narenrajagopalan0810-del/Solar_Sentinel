"""
SonarSentinel — Step 7: Report Export Endpoint (report.py)
===========================================================
Build Order Reference : SonarSentinel_Backend_Build_Order.txt  →  Step 7
Depends on           : Step 6 (Geotagging Engine)

WHAT THIS FILE DOES
-------------------
Adds a POST /api/report endpoint that:
  1. Accepts the final list of detections, vessel telemetry, and mission metadata.
  2. Serializes the data into downloadable JSON or CSV format.
  3. Returns a downloadable Response attachment.
"""

import io
import csv
import json
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Response
from pydantic import BaseModel, Field

logger = logging.getLogger("sonarsentinel.step7.report")

# ---------------------------------------------------------------------------
# Pydantic schemas for the Report request body
# ---------------------------------------------------------------------------

class ReportBoundingBox(BaseModel):
    """Pixel coordinates in original image space."""
    x1: float = Field(..., description="Top-left X pixel coordinate")
    y1: float = Field(..., description="Top-left Y pixel coordinate")
    x2: float = Field(..., description="Bottom-right X pixel coordinate")
    y2: float = Field(..., description="Bottom-right Y pixel coordinate")
    width:  float = Field(..., description="Box width in pixels")
    height: float = Field(..., description="Box height in pixels")


class ReportDetection(BaseModel):
    """Georeferenced detection with physics verification results."""
    detection_id: str  = Field(..., description="Sequential ID e.g. DET-01")
    class_name:   str  = Field(..., description="Predicted target class")
    confidence:   float = Field(..., description="Final detection confidence score")
    bbox: ReportBoundingBox
    latitude: float = Field(..., description="Estimated WGS84 latitude")
    longitude: float = Field(..., description="Estimated WGS84 longitude")
    crop_image_url: Optional[str] = Field(default=None, description="Path or base64 data URL for thumbnail crop")
    shadow_detected: Optional[bool] = Field(default=False, description="True if shadow was verified")
    acoustic_score: Optional[float] = Field(default=None, description="Acoustic physics score")
    final_score: Optional[float] = Field(default=None, description="Blended final hazard score")
    hazard_level: Optional[str] = Field(default=None, description="Computed hazard severity level")


class ReportRequest(BaseModel):
    """Payload containing mission metadata, navigation sidecar, and detection list."""
    mission_id: str = Field(..., description="Unique mission ID")
    mission_name: str = Field(default="MoES-Survey-Alpha", description="Mission or transect label")
    vessel_lat: float = Field(..., description="Vessel latitude on WGS84 grid")
    vessel_lon: float = Field(..., description="Vessel longitude on WGS84 grid")
    heading: float = Field(..., description="Vessel True Heading in degrees [0-360]")
    altitude: float = Field(..., description="Towfish altitude above seabed in meters")
    swath_width_m: float = Field(..., description="Total sonar swath width in meters")
    detections: List[ReportDetection] = Field(..., description="Final georeferenced detections")


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(tags=["Step 7 — Report Export"])


# ---------------------------------------------------------------------------
# Serialization Helpers
# ---------------------------------------------------------------------------

def generate_csv_report(req: ReportRequest) -> str:
    """Generates a downloadable CSV document."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write Metadata Headers
    writer.writerow(["# SonarSentinel Mission Export Report"])
    writer.writerow(["# Mission ID", req.mission_id])
    writer.writerow(["# Mission Name", req.mission_name])
    writer.writerow(["# Vessel Lat", req.vessel_lat])
    writer.writerow(["# Vessel Lon", req.vessel_lon])
    writer.writerow(["# Heading (deg)", req.heading])
    writer.writerow(["# Altitude (m)", req.altitude])
    writer.writerow(["# Swath Width (m)", req.swath_width_m])
    writer.writerow(["# Total Detections", len(req.detections)])
    writer.writerow([])

    # Table Column Headers
    writer.writerow([
        "Detection ID",
        "Class Name",
        "Confidence",
        "Latitude (WGS84)",
        "Longitude (WGS84)",
        "BBox X1",
        "BBox Y1",
        "BBox X2",
        "BBox Y2",
        "Crop Width",
        "Crop Height",
        "Thumbnail Crop Path"
    ])

    for det in req.detections:
        writer.writerow([
            det.detection_id,
            det.class_name,
            f"{det.confidence:.2f}",
            f"{det.latitude:.6f}",
            f"{det.longitude:.6f}",
            int(det.bbox.x1),
            int(det.bbox.y1),
            int(det.bbox.x2),
            int(det.bbox.y2),
            int(det.bbox.width),
            int(det.bbox.height),
            det.crop_image_url or "N/A"
        ])

    return output.getvalue()


# ---------------------------------------------------------------------------
# API Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/report",
    summary="Generate Downloadable Mission Report — Step 7",
    description=(
        "Accepts a list of final geotagged detections along with vessel telemetry "
        "and serializes it to downloadable JSON or CSV format."
    )
)
async def export_report(
    request_data: ReportRequest,
    format: str = Query(
        default="json",
        pattern="^(json|csv)$",
        description="Desired output format — 'json' or 'csv'"
    )
) -> Response:
    """
    POST /api/report
    """
    try:
        if format == "json":
            json_str = request_data.model_dump_json(indent=2)
            return Response(
                content=json_str,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=SonarSentinel_Report_{request_data.mission_id}.json"
                }
            )
        elif format == "csv":
            csv_str = generate_csv_report(request_data)
            return Response(
                content=csv_str,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=SonarSentinel_Report_{request_data.mission_id}.csv"
                }
            )
    except Exception as exc:
        logger.error(f"[Step 7] Report serialization failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {exc}")

    raise HTTPException(status_code=400, detail="Invalid format type specified.")
